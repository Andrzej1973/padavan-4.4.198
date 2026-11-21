#!/usr/bin/env python3
"""Actual runtime backend and configuration owner; native/SDK boundaries injected."""
from pathlib import Path
import ast
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
source = (here / "check-rc-backend-composition.py").read_text()
ns = {"__file__": str(here / "check-rc-backend-composition.py")}
exec(compile(source[:source.index("with tempfile.TemporaryDirectory(")], "<backend setup>", "exec"), ns)
units = next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source))
             if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "units" for t in n.targets))
body = ns["body"]
hooks = r'''
#include "config-owner.h"
#include "profile-history.h"
/* Configuration-only fixture retains injected profile/SDK boundaries. It does
 * not compose radio generation; absent file history must not become proof. */
int wr_iot_rc_profile_history_read(struct wr_iot_profile_binding*b,struct wr_iot_restart_profile_receipt*p){
 assert(depth);memset(b,0,sizeof(*b));memset(p,0,sizeof(*p));return 0;
}
int wr_iot_rc_profile_history_active(void){assert(depth);return 0;}

static char cfg_record[WR_IOT_SAVED_CONFIG_MAX];
static int cfg_present,cfg_writes,cfg_read_error;
int nvram_getall(char *out,int capacity,int temporary){
 assert(capacity==0x20000&&temporary==1&&depth);
 if(cfg_read_error)return -1;
 memset(out,0,(size_t)capacity);
 if(cfg_present)snprintf(out,(size_t)capacity,"%s=%s",WR_IOT_SAVED_CONFIG_KEY,cfg_record);
 return 0;
}
int nvram_set(const char *key,const char *value){
 assert(depth>=2&&!strcmp(key,WR_IOT_SAVED_CONFIG_KEY));
 cfg_writes++;strcpy(cfg_record,value);cfg_present=1;return 0;
}
'''
anchor = "int main(void){"
assert body.count(anchor) == 1
body = body.replace(anchor, hooks + anchor, 1)
anchor = "int main(void){\n reset();idle_reads=0;rollback_dns=0;"
assert body.count(anchor) == 1
body = body.replace(anchor, anchor + r'''
 {
  struct wr_iot_config_backend baseline={0},before;
  wr_iot_rc_shutdown.active=1;int token=wr_iot_service_guard_enter(1);
  assert(token==1&&wr_iot_rc_config_backend_capture(&baseline));
  assert(baseline.kind==WR_IOT_CONFIG_BACKEND_IDLE&&!baseline.id[0]&&!baseline.created);
  before=baseline;backend.busy=1;
  assert(!wr_iot_rc_config_backend_capture(&baseline)&&!memcmp(&baseline,&before,sizeof(baseline)));
  backend.busy=0;assert(wr_iot_rc_config_backend_current(&baseline));
  wr_iot_service_guard_leave(token);wr_iot_rc_shutdown.active=0;
 }
''', 1)
anchor = " terminal(on.id);assert(!wr_iot_rc_continue());"
exercise = r'''
 {
  struct wr_iot_config_owner config_owner={0},moved;
  struct wr_iot_saved_config desired={.profile={.enabled=0,.ssid="Next IoT",
   .password="next-password",.gateway="192.168.60.1",.mask="255.255.255.0",
   .first="192.168.60.20",.last="192.168.60.200"}};
  const char *config_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
  struct wr_iot_request loaded=backend.start.input.request;
  assert(wr_iot_rc_shutdown.normal_route_armed);
  wr_iot_rc_shutdown.normal_route_armed=0;
  assert(!wr_iot_config_owner_begin(&config_owner,config_id,20,&desired)&&!depth&&!cfg_writes);
  assert(!wr_iot_rc_shutdown.active&&!config_owner.owner);
  wr_iot_rc_shutdown.normal_route_armed=1;
  assert(wr_iot_config_owner_begin(&config_owner,config_id,19,&desired));
  cfg_read_error=1;
  assert(wr_iot_config_owner_step(&config_owner,config_id,19,1)==WR_IOT_CONFIG_RECOVERY&&!cfg_writes);
  cfg_read_error=0;
  assert(wr_iot_config_owner_step(&config_owner,config_id,19,1)==WR_IOT_CONFIG_REJECTED&&!cfg_writes);
  assert(wr_iot_config_owner_finish(&config_owner,config_id,19)&&!depth);
  assert(wr_iot_config_owner_retire(&config_owner));
  assert(wr_iot_config_owner_begin(&config_owner,config_id,20,&desired));
  assert(config_owner.backend.kind==WR_IOT_CONFIG_BACKEND_ACTIVE&&depth==2);
  assert(!strcmp(config_owner.backend.id,on.id)&&strcmp(config_id,on.id));
  assert(!wr_iot_config_owner_begin(&config_owner,config_id,20,&desired));
  moved=config_owner;
  assert(wr_iot_config_owner_step(&moved,config_id,20,0)==WR_IOT_CONFIG_RECOVERY&&!cfg_writes);
  assert(!wr_iot_config_owner_observed(&config_owner,config_id,21));
  assert(wr_iot_config_owner_step(&config_owner,config_id,20,0)==WR_IOT_CONFIG_RAM_READY&&cfg_writes==1);
  assert(!memcmp(&loaded,&backend.start.input.request,sizeof(loaded))&&backend.phase==WR_IOT_OWNER_ACTIVE);
  assert(wr_iot_config_owner_observed(&config_owner,config_id,20)&&cfg_writes==1);
  assert(wr_iot_config_owner_step(&config_owner,config_id,20,0)==WR_IOT_CONFIG_RAM_READY&&cfg_writes==1);
  backend.owner++;
  assert(wr_iot_config_owner_step(&config_owner,config_id,20,0)==WR_IOT_CONFIG_RECOVERY&&depth==2&&cfg_writes==1);
  assert(!wr_iot_config_owner_finish(&config_owner,config_id,20));backend.owner--;
  assert(wr_iot_config_owner_step(&config_owner,config_id,20,0)==WR_IOT_CONFIG_RAM_READY&&cfg_writes==1);
  assert(signal(SIGTERM,signal_handler)!=SIG_ERR);
  assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.pending==SIGTERM);
  cfg_read_error=1;
  assert(!wr_iot_config_owner_finish(&config_owner,config_id,20)&&depth==2&&wr_iot_rc_shutdown.active);
  cfg_read_error=0;assert(wr_iot_config_owner_finish(&config_owner,config_id,20));
  assert(!depth&&!wr_iot_rc_shutdown.active&&!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
  assert(config_owner.phase==WR_IOT_CONFIG_RAM_COMMITTED&&!config_owner.store.owner);
  assert(wr_iot_config_owner_observed(&config_owner,config_id,20)&&!depth&&cfg_writes==1);
  cfg_record[0]='X';assert(!wr_iot_config_owner_observed(&config_owner,config_id,20));
  cfg_record[0]='W';assert(wr_iot_config_owner_observed(&config_owner,config_id,20));
  assert(wr_iot_config_owner_retire(&config_owner));
  /* Backend-only fixture has a normal-consumer actor; its routed request is
   * explicitly cleared here to continue the independent ordinary OFF case.
   * Actual normal/physical shutdown is covered by the separate full composition. */
  wr_iot_rc_shutdown.normal_route_requested=0;
  assert(wr_iot_config_owner_begin(&config_owner,config_id,21,&desired));
  assert(wr_iot_config_owner_step(&config_owner,config_id,21,1)==WR_IOT_CONFIG_REJECTED&&cfg_writes==1);
  assert(wr_iot_config_owner_finish(&config_owner,config_id,21)&&!depth);
  assert(wr_iot_config_owner_retire(&config_owner));
 }
'''
assert body.count(anchor) == 1
body = body.replace(anchor, anchor + exercise, 1)
anchor = " terminal(off.id);assert(!wr_iot_rc_continue());"
assert body.count(anchor) == 1
body = body.replace(anchor, anchor + r'''
 {
  struct wr_iot_config_backend baseline={0};
  int routed=wr_iot_rc_shutdown.normal_route_requested;
  wr_iot_rc_shutdown.normal_route_requested=0;wr_iot_rc_shutdown.active=1;
  int token=wr_iot_service_guard_enter(1);assert(token==1);
  assert(wr_iot_rc_config_backend_capture(&baseline)&&baseline.kind==WR_IOT_CONFIG_BACKEND_OFF);
  assert(!strcmp(baseline.id,off.id)&&baseline.created==off.created);
  assert(wr_iot_rc_config_backend_current(&baseline));
  wr_iot_service_guard_leave(token);wr_iot_rc_shutdown.active=0;
  wr_iot_rc_shutdown.normal_route_requested=routed;
 }
''', 1)
shared = here.parent / "band-steering"
with tempfile.TemporaryDirectory(prefix="wr-config-backend-") as directory:
    root = Path(directory)
    subprocess.run([sys.executable, str(here / "prepare-request-stage-check.py"), directory], check=True)
    with (root / "rc.h").open("a") as f:
        f.write("\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n")
    (root / "wr-band-settings-snapshot.h").write_bytes((shared / "settings-snapshot.h").read_bytes())
    unit = root / "check.c"
    unit.write_text(ns["prefix"] + '\n#include "check-reopen-unused.h"\n' + body)
    binary = root / "check"
    subprocess.run([
        "gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
        "-fsanitize=address,undefined", "-fno-pie", "-no-pie",
        "-DWR_IOT_NATIVE_NVRAM_SPACE=61440", "-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20",
        "-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1", "-I" + directory, "-I" + str(here),
        str(unit), *[str(here / n) for n in units], str(here / "config-owner.c"),
        str(here / "saved-config-store.c"), str(shared / "settings-snapshot.c"),
        "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True, timeout=30)
print("PASS actual config owner/store + retained ACTIVE backend: distinct transaction, no loaded-profile mutation, publication retry, stale backend retention, fresh RAM receipt, pending TERM routed after cleanup; native/SDK/normal-consumer actors, no flash/device acceptance")
