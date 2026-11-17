#!/usr/bin/env python3
"""Real queue/client/RC facade/owner/fork worker; native SDK/flash actors."""
from pathlib import Path
import ast
import subprocess
import tempfile
here=Path(__file__).resolve().parent;shared=here.parent/'band-steering'
tree=ast.parse((here/'check-config-save-owner.py').read_text())
body=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
body=body[:body.index('int main(void){')]
body=body.replace('struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;','')
# Keep helpers used by the actual owner fixture to validate same-path ownership.
body+=r'''
#include "control-channel.h"
#include "config-save-server.h"
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *r){(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}
enum wr_iot_result_state wr_iot_activation_continue(const char *id,unsigned long long t){(void)id;(void)t;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_backend_applied_route(const char *id,unsigned long long t){(void)id;(void)t;assert(0);return 0;}
enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *r){(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}
enum wr_iot_result_state wr_iot_rc_config_continue(const char *id,unsigned long long t){(void)id;(void)t;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *r){(void)r;assert(0);return 0;}
int wr_iot_activation_result_observed(const struct wr_iot_control_result *r){(void)r;assert(0);return 0;}
/* Private IPC separately tested; call actual RC Save observer here. */
int wr_iot_configuration_result_observed(const struct wr_iot_control_result *r){return wr_iot_rc_save_observed(r);}
int main(int argc,char **argv){
 struct sigaction action={0};char request_id[33],file[PATH_MAX];struct wr_iot_control_result result;
 int i,mode=argc>1?atoi(argv[1]):0,before;
 (void)id;(void)drain;
 m=mmap(NULL,sizeof(*m),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);assert(m!=MAP_FAILED);
 action.sa_handler=reaper;sigemptyset(&action.sa_mask);assert(!sigaction(SIGCHLD,&action,NULL));reset();
 wr_iot_rc_shutdown.active=0;
 assert(wr_iot_rc_save_backend_install());m->manual=mode==1;m->unknown=mode==2;m->allow=1;before=reaped;
 assert(wr_iot_rc_submit_save(&config,mode==1?0:1,request_id));
 assert(wr_iot_rc_dispatch()&&wr_iot_rc_pending());
 for(i=0;i<1000&&wr_iot_rc_pending();i++){
  assert(wr_iot_rc_continue());
  if(mode==2&&m->commits&&reaped>before)break;
  usleep(5000);
 }
 wait_reap(before);
 assert(m->writes==1&&m->commits==(mode==1?0:1));
 if(mode==2){
  assert(wr_iot_rc_pending()&&wr_iot_rc_shutdown.active);
  for(i=0;i<10;i++)assert(wr_iot_rc_continue()&&m->writes==1&&m->commits==1);
  assert(wr_iot_rc_status(request_id,&result)&&result.state==WR_IOT_RESULT_RECOVERY);
 }else{
  assert(!wr_iot_rc_pending()&&!wr_iot_rc_shutdown.active);
  assert(wr_iot_rc_status(request_id,&result));
  assert(result.state==(mode==1?WR_IOT_RESULT_STORED_RAM:WR_IOT_RESULT_SAVED_FLASH));
  assert(!wr_iot_rc_continue()&&m->writes==1&&m->commits==(mode==1?0:1));
  strcpy(m->record,"foreign");assert(!wr_iot_rc_status(request_id,&result));
 }
 /* Only isolated fixture files; no production recovery/unknown release. */
 snprintf(file,sizeof(file),"%s/request",WR_IOT_CONTROL_DIRECTORY);if(!access(file,F_OK))assert(!unlink(file));
 snprintf(file,sizeof(file),"%s/result",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));
 snprintf(file,sizeof(file),"%s/lock",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));assert(!rmdir(WR_IOT_CONTROL_DIRECTORY));
 munmap((void*)m,sizeof(*m));return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-save-route-') as directory:
 root=Path(directory);source=root/'check.c';binary=root/'check';source.write_text('#include <stdlib.h>\n'+body)
 (root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 units=('control-client','control-mailbox','control-server','config-save-server','config-save-owner','config-owner','saved-config-store','flash-worker','flash-save-attempt','service-guard')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
 '-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED=1','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
 '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
 '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'service.lock')+'"','-DWR_IOT_CONTROL_DIRECTORY="'+str(root/'queue')+'"',
 '-DWR_IOT_NOTIFY()=((void)0)','-I'+str(root),'-I'+str(here),str(source),
 *[str(here/(unit+'.c')) for unit in units],str(shared/'settings-snapshot.c'),'-o',str(binary)],check=True)
 for mode in range(3):subprocess.run([str(binary),str(mode)],check=True,timeout=25)
print('PASS actual Save client/queue/RC registration/facade/owner/store/parser/guard/fork worker: flash, manual RAM-only, unknown no-replay/admission retention and changed-RAM status refusal; native flash and private IPC actors')
