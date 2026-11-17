"""Actual CGI/mailbox ON publication arms normal shutdown without explicit arm.
Fresh backend and unavailable consumer cases retain private terminal ownership.
"""
from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-normal-shutdown-backend-composition.py').read_text()
ns={'__file__':str(here/'check-normal-shutdown-backend-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<normal backend setup>','exec'),ns)
body=ns['body']
a='normal_entropy=1;assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!shutdowns);'
assert body.count(a)==1
body=body.replace(a,'normal_entropy=1;assert(wr_iot_rc_shutdown.normal_route_armed&&!raise(SIGTERM)&&!shutdowns);',1)
hook='static int terminal_test_mode,terminal_hook_calls;\nstatic void mailbox_terminal_hook(void){\n if(backend.phase!=WR_IOT_OWNER_ACTIVE){assert(backend.phase==WR_IOT_OWNER_INITIAL_OFF);return;}\n terminal_hook_calls++;\n assert(wr_iot_continuation.active&&wr_iot_continuation.terminal&&\n  wr_iot_continuation.outcome==WR_IOT_RESULT_APPLIED&&backend.phase==WR_IOT_OWNER_ACTIVE);\n if(terminal_hook_calls==1){\n  if(terminal_test_mode==1||terminal_test_mode==3)normal_shutdown.spent=1;\n  if(terminal_test_mode==2||terminal_test_mode==3)assert(!raise(SIGTERM));\n  if(terminal_test_mode==4)live_epoch++;\n }else{\n  assert(terminal_hook_calls==2&&wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.normal_route_armed);\n  struct wr_iot_mailbox m;struct wr_iot_control_result result={0};wr_iot_mailbox_init(&m);\n  assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0));\n  assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_RECOVERY&&\n   !strcmp(result.id,wr_iot_continuation.id)&&result.created==wr_iot_continuation.created);\n  wr_iot_mailbox_close(&m);\n  assert(!normal_shutdown.generated&&!normal_shutdown.claimed&&!physical.owner&&!closes);\n  if(terminal_test_mode==1||terminal_test_mode==3){assert(normal_shutdown.spent);normal_shutdown.spent=0;}\n  if(terminal_test_mode==4)live_epoch--;\n }\n}\n\n'
a='static void routed_signal(int sig){';assert body.count(a)==1;body=body.replace(a,hook+'\n'+a,1)
body=body.replace('int main(void){','int main(int argc,char **argv){\n assert(argc==2);terminal_test_mode=atoi(argv[1]);assert(terminal_test_mode>=0&&terminal_test_mode<=4);',1)
a=' submit(&on);wr_iot_rc_shutdown.radio_off_owned=1;';assert body.count(a)==1
body=body.replace(a,''' /* Factory INITIAL_OFF requires empty runtime credentials. */
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 strcpy(off.id,"01010101010101010101010101010102");
 normal_shutdown.spent=1;submit(&off);
 assert(wr_iot_rc_dispatch()&&!wr_iot_rc_shutdown.active&&backend.phase==WR_IOT_OWNER_INITIAL_OFF);
 assert(!wr_iot_rc_shutdown.normal_route_armed&&!wr_iot_continuation.active&&normal_shutdown.spent);
 terminal(off.id);normal_shutdown.spent=0;
'''+a,1)
a='assert(!wr_iot_rc_dispatch()&&!wr_iot_rc_shutdown.active&&!wr_iot_continuation.active&&backend.phase==WR_IOT_OWNER_IDLE);'
assert body.count(a)==1;body=body.replace(a,a.replace('WR_IOT_OWNER_IDLE','WR_IOT_OWNER_INITIAL_OFF'),1)
with tempfile.TemporaryDirectory(prefix='wr-mailbox-active-shutdown-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 server=(here/'control-server.c').read_text()
 server=server.replace('#include "rc-shutdown-admission.h"','#include "rc-shutdown-admission.h"\nstatic void mailbox_terminal_hook(void);',1)
 a=' terminal_ready=wr_iot_continuation.terminal&&';assert server.count(a)==2
 server=server.replace(a,' if(wr_iot_continuation.terminal&&outcome==WR_IOT_RESULT_APPLIED)mailbox_terminal_hook();\n'+a)
 (Path(d)/'control-server.c').write_text(server)
 cursor=ns
 while 'prefix' not in cursor:cursor=cursor['ns']
 prefix=cursor['prefix']
 cursor=ns
 while 'units' not in cursor:cursor=cursor['ns']
 p=Path(d)/'test.c';p.write_text(prefix+'\n#include "check-reopen-unused.h"\n'+body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),*[str(here/n) for n in cursor['units']],str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 for mode in range(5):
  subprocess.run([d+'/check',str(mode)],check=True,timeout=20)
  print('PASS mailbox active terminal handoff mode='+str(mode),flush=True)
