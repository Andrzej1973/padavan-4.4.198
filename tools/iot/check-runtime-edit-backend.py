"""Compose edit lease with the actual retained RC backend/runner/normal OFF."""
from pathlib import Path
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
source=(here/'check-config-owner-backend.py').read_text()
ns={'__file__':str(here/'check-config-owner-backend.py')}
exec(compile(source[:source.rindex('\nwith tempfile.TemporaryDirectory(')],'<backend fixture setup>','exec'),ns)
body=ns['body'].split('int main(void){',1)[0]
body=body.replace('return wr_iot_rc_backend_observed(r);','return wr_iot_rc_edit_observed(r);')
assert body.count('#include "control-server.c"')==1
body=body.replace('#include "control-server.c"','#include "config-edit-server.h"\n#include "control-server.c"')
body+=r'''
#include "config-save-server.h"
enum wr_iot_result_state wr_iot_rc_save_execute(const struct wr_iot_control_request*r){(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}
enum wr_iot_result_state wr_iot_rc_save_continue(const char*id,unsigned long long t){(void)id;(void)t;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_save_terminal_ready(const struct wr_iot_control_result*r){(void)r;assert(0);return 0;}
int wr_iot_rc_save_observed(const struct wr_iot_control_result*r){(void)r;assert(0);return 0;}
static unsigned char edit_entropy_value=0x5a;
unsigned long long fixture_edit_clock(void){return 10;}
int fixture_edit_entropy(void*unused,unsigned char*bytes,unsigned length){assert(!unused&&length==32);memset(bytes,edit_entropy_value++,length);return 32;}
static void toggle(const struct wr_iot_saved_config *config,int enabled,char digit){
 struct wr_iot_config_view view;char revision[33];
 struct wr_iot_control_request request={0};struct wr_iot_mailbox mailbox;
 assert(wr_iot_rc_edit_view(30,&view,revision)&&view.key_present==1);
 memset(request.id,digit,32);
 if(enabled)memcpy(request.id,"01010101010101010101010101010101",33);
 request.created=wr_iot_control_now();
 request.operation=WR_IOT_OPERATION_CONFIG_EDIT_RUNTIME;
 memcpy(request.edit.id,request.id,33);request.edit.created=request.created;
 memcpy(request.edit.revision,revision,33);request.edit.mode=WR_IOT_EDIT_RUNTIME;
 request.edit.action=WR_IOT_CONFIG_KEY_KEEP;request.edit.fields=*config;
 request.edit.fields.profile.enabled=enabled;
 memset(request.edit.fields.profile.password,0,sizeof(request.edit.fields.profile.password));
 wr_iot_mailbox_init(&mailbox);assert(wr_iot_mailbox_open(&mailbox,mailbox_directory,1));
 assert(wr_iot_mailbox_submit(&mailbox,&request));wr_iot_mailbox_close(&mailbox);
 assert(wr_iot_rc_dispatch());
 if(!enabled){
  for(int i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)assert(wr_iot_rc_continue());
  assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3&&closes==1);
  quarantine_ready=0;
  for(int i=0;i<3;i++)assert(wr_iot_rc_continue()&&closes==1&&depth==3);
  assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.pending==SIGTERM);
  quarantine_ready=1;
 }
 for(int i=0;i<100&&wr_iot_rc_pending();i++)assert(wr_iot_rc_continue());
 assert(!wr_iot_rc_pending()&&!wr_iot_rc_shutdown.active&&!depth);
 terminal(request.id);
}
int main(void){
 (void)submit;(void)signal_handler;(void)candidate_read;
 struct wr_iot_saved_config desired={.profile={.enabled=0,.ssid="IoT",.password="password123",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 reset();idle_reads=0;rollback_dns=0;wr_iot_rc_shutdown.active=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 cfg_present=1;assert(wr_iot_saved_config_encode(cfg_record,sizeof(cfg_record),&desired));
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(mkdtemp(mailbox_directory)&&wr_iot_rc_edit_backend_install());
 assert(signal(SIGTERM,signal_handler)!=SIG_ERR);
 /* 01 bytes retain the existing driver fixture's OPEN challenge identity. */
 toggle(&desired,1,'1');
 assert(backend.phase==WR_IOT_OWNER_ACTIVE&&wr_iot_rc_shutdown.normal_route_armed&&!cfg_writes);
 struct wr_iot_request loaded=backend.start.input.request;
 strcpy(desired.profile.ssid,"Next desired IoT");strcpy(desired.profile.password,"next-password");
 assert(wr_iot_saved_config_encode(cfg_record,sizeof(cfg_record),&desired));
 assert(!memcmp(&loaded,&backend.start.input.request,sizeof(loaded)));
 toggle(&desired,0,'2');
 assert(backend.phase==WR_IOT_OWNER_OFF&&!cfg_writes&&closes==1&&progresses==1&&releases==1);
 assert(!shutdowns&&!wr_iot_rc_shutdown.pending&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 struct wr_iot_saved_config after={0};assert(wr_iot_saved_config_decode(&after,cfg_record,strlen(cfg_record)));
 assert(!strcmp(after.profile.ssid,"Next desired IoT")&&!strcmp(after.profile.password,"next-password"));
 struct wr_iot_request empty={0};assert(!memcmp(&backend.start.input.request,&empty,sizeof(empty)));
 char path[PATH_MAX];for(unsigned i=0;i<2;i++){
  assert(snprintf(path,sizeof(path),"%s/%s",mailbox_directory,i?"lock":"result")<(int)sizeof(path));assert(!unlink(path));
 }
 assert(!rmdir(mailbox_directory));
 puts("PASS runtime edit lease/mailbox/actual RC backend/owner/runner/OFF: changed desired credentials retain old close identity, failed isolation holds guards, pending real SIGTERM routed after one close/progress/release and terminal cleanup, no desired SET/Save; driver/network/guard/normal-consumer actors, no RF/device acceptance");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-runtime-edit-backend-') as directory:
 root=Path(directory)
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),directory],check=True)
 with (root/'rc.h').open('a') as f:f.write('\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 shared=here.parent/'band-steering'
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 unit=root/'check.c';unit.write_text(ns['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
  '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED=1',
  '-DWR_IOT_EDIT_CLOCK=fixture_edit_clock','-DWR_IOT_EDIT_ENTROPY=fixture_edit_entropy',
  '-I'+directory,'-I'+str(here),str(unit),*[str(here/n) for n in ns['units']],
  str(here/'saved-config-store.c'),str(here/'config-edit-server.c'),str(shared/'settings-snapshot.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=30)
