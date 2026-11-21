#!/usr/bin/env python3
"""Real single-slot client/mailbox/server plus actual config/runtime owners."""
from pathlib import Path
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
source = (here / "check-config-owner-backend.py").read_text()
setup = {"__file__": str(here / "check-config-owner-backend.py")}
exec(compile(source[:source.index("\nwith tempfile.TemporaryDirectory(")], "<config owner setup>", "exec"), setup)
body = setup["body"]
a = "static int cfg_present,cfg_writes,cfg_read_error;"
assert body.count(a) == 1
body = body.replace(a, a + r'''
static int cfg_block_publication,cfg_emit_shutdown;
int wr_iot_configuration_result_observed(const struct wr_iot_control_result *r)
{return wr_iot_rc_config_observed(r);}
''', 1)
a = "cfg_writes++;strcpy(cfg_record,value);cfg_present=1;return 0;"
assert body.count(a) == 1
body = body.replace(a, r'''
 cfg_writes++;strcpy(cfg_record,value);cfg_present=1;
 if(cfg_block_publication){char path[PATH_MAX];int fd;
  cfg_block_publication=0;
  assert(snprintf(path,sizeof(path),"%s/result.new",mailbox_directory)<(int)sizeof(path));
  fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0600);assert(fd>=0);
  assert(write(fd,"held",4)==4&&!close(fd));
 }
 if(cfg_emit_shutdown){cfg_emit_shutdown=0;assert(!raise(SIGTERM));}
 return 0;
''', 1)
exercise = r'''
 {
  struct wr_iot_saved_config desired={.profile={.enabled=0,.ssid="Transport IoT",
   .password="transport-password",.gateway="192.168.61.1",.mask="255.255.255.0",
   .first="192.168.61.20",.last="192.168.61.200"}};
  struct wr_iot_control_result stored={0};struct wr_iot_mailbox queue;
  struct wr_iot_request loaded=backend.start.input.request;
  char config_id[33],path[PATH_MAX];int before_writes=cfg_writes;
  {struct wr_iot_control_request wrong={.id="cccccccccccccccccccccccccccccccc",.created=1,
    .operation=WR_IOT_OPERATION_CONFIG};wrong.request=desired.profile;
   wr_iot_rc_shutdown.active=1;
   assert(wr_iot_activation_execute(&wrong)==WR_IOT_RESULT_REJECTED&&!depth);
   assert(backend.phase==WR_IOT_OWNER_ACTIVE&&cfg_writes==before_writes);
   wr_iot_rc_shutdown.active=0;
  }
  assert(wr_iot_rc_submit_config(&desired,config_id));
  assert(wr_iot_rc_dispatch()&&wr_iot_rc_pending()&&depth==2);
  assert(wr_iot_continuation.operation==WR_IOT_OPERATION_CONFIG&&!wr_iot_continuation.terminal);
  assert(cfg_writes==before_writes&&backend.phase==WR_IOT_OWNER_ACTIVE);
  cfg_block_publication=cfg_emit_shutdown=1;
  assert(signal(SIGTERM,signal_handler)!=SIG_ERR);
  assert(!wr_iot_rc_continue()&&wr_iot_rc_pending()&&cfg_writes==before_writes+1);
  assert(wr_iot_continuation.terminal&&wr_iot_continuation.outcome==WR_IOT_RESULT_STORED_RAM);
  assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM&&!shutdowns&&!depth);
  assert(!memcmp(&loaded,&backend.start.input.request,sizeof(loaded)));
  wr_iot_mailbox_init(&queue);assert(wr_iot_mailbox_open(&queue,mailbox_directory,0));
  assert(wr_iot_mailbox_result(&queue,&stored)&&stored.state==WR_IOT_RESULT_RECOVERY);
  assert(!faccessat(queue.directory,"request",F_OK,0));wr_iot_mailbox_close(&queue);
  cfg_read_error=1;
  assert(!wr_iot_rc_continue()&&wr_iot_rc_pending()&&cfg_writes==before_writes+1);
  cfg_read_error=0;
  assert(snprintf(path,sizeof(path),"%s/result.new",mailbox_directory)<(int)sizeof(path));
  assert(!unlink(path));
  assert(wr_iot_rc_continue()&&!wr_iot_rc_pending()&&cfg_writes==before_writes+1);
  assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&!shutdowns);
  assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&!depth);
  assert(wr_iot_rc_status(config_id,&stored)&&stored.state==WR_IOT_RESULT_STORED_RAM);
  assert(!strcmp(wr_iot_control_state(stored.state),"stored_in_ram"));
  assert(!wr_iot_rc_continue()&&cfg_writes==before_writes+1);
  cfg_record[0]='X';assert(!wr_iot_rc_status(config_id,&stored));cfg_record[0]='W';
  assert(wr_iot_rc_status(config_id,&stored)&&stored.state==WR_IOT_RESULT_STORED_RAM);
  /* Fixture-only boundary: actual normal/physical handling has its own test. */
  wr_iot_rc_shutdown.normal_route_requested=0;
 }
'''
anchor = " submit(&off);assert(wr_iot_rc_dispatch()&&wr_iot_rc_shutdown.active);"
assert body.count(anchor) == 1
body = body.replace(anchor, exercise + anchor, 1)
shared = here.parent / "band-steering"
with tempfile.TemporaryDirectory(prefix="wr-config-channel-") as directory:
    root = Path(directory)
    subprocess.run([sys.executable, str(here / "prepare-request-stage-check.py"), directory], check=True)
    with (root / "rc.h").open("a") as f:
        f.write("\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n")
    (root / "wr-band-settings-snapshot.h").write_bytes((shared / "settings-snapshot.h").read_bytes())
    unit = root / "check.c"
    unit.write_text(setup["ns"]["prefix"] + '\n#include "check-reopen-unused.h"\n' + body)
    binary = root / "check"
    subprocess.run([
        "gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
        "-fsanitize=address,undefined", "-fno-pie", "-no-pie",
        "-DWR_IOT_NATIVE_NVRAM_SPACE=61440", "-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20",
        "-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1", "-DWR_IOT_TEST_CONFIG_SERVER_REAL=1",
        "-I" + directory, "-I" + str(here), str(unit),
        *[str(here / n) for n in setup["units"]], str(here / "config-server.c"),
        str(here / "config-owner.c"), str(here / "saved-config-store.c"),
        str(shared / "settings-snapshot.c"), "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True, timeout=30)
print("PASS actual typed config client/mailbox/server/owner/store: retained RAM receipt before publication, no SET replay, pending TERM fenced, fresh distinct status, ordinary OFF afterward; IPC observer/SDK/native/normal boundaries injected")
