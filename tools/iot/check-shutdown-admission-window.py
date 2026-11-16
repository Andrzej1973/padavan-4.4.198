"""Real TERM/QUIT between admission check/publication, through actual RC mailbox."""
from pathlib import Path
import ast,subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-backend-composition.py').read_text()
ns={'__file__':str(here/'check-rc-backend-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<RC fixture setup>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
body=ns['body'].split('int main(void){',1)[0]
a='static char mailbox_directory[]="/tmp/iot-rc-owner-mailbox-XXXXXX";'
assert a in body;body=body.replace(a,'static char mailbox_directory[PATH_MAX];',1)
pre=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <limits.h>
#include <signal.h>
static int window_mode,window_signal,window_seen,duplicate_seen;
static void admission_before_publish(void);
static void admission_duplicate(void);
#include "admission-under-test.h"
'''
main=r'''
static void window_handler(int sig){if(!wr_iot_rc_shutdown_note(sig))shutdowns++;}
static void admission_before_publish(void){assert(!wr_iot_rc_shutdown.active);window_seen++;assert(!raise(window_signal));}
static void admission_duplicate(void){
 if(window_mode!=2)return;
 duplicate_seen++;
 assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.normal_route_requested==window_signal);
 assert(!raise(window_signal==SIGTERM?SIGQUIT:SIGTERM));
 assert(wr_iot_rc_shutdown.pending&&!shutdowns);
}
int main(int argc,char **argv){
 (void)signal_handler;(void)terminal;(void)admission_duplicate;
 assert(argc==4);window_mode=atoi(argv[2]);window_signal=atoi(argv[3])?SIGQUIT:SIGTERM;
 reset();assert(snprintf(mailbox_directory,sizeof(mailbox_directory),"%s/mailbox-XXXXXX",argv[1])<(int)sizeof(mailbox_directory));
 assert(mkdtemp(mailbox_directory));
 struct sigaction sa={0};sa.sa_handler=window_handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,0)&&!sigaction(SIGQUIT,&sa,0));
 struct wr_iot_control_request on={.id="01010101010101010101010101010101",.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 submit(&on);struct wr_iot_activation_owner before=backend;
 assert(wr_iot_rc_shutdown_route_arm());
 assert(!wr_iot_rc_dispatch());
 assert(window_seen==1&&duplicate_seen==(window_mode==2));
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&!wr_iot_continuation.active);
 assert(wr_iot_rc_shutdown.normal_route_requested==window_signal&&!shutdowns);
 assert(!depth&&!mode_reads&&!memcmp(&before,&backend,sizeof(backend)));
 struct wr_iot_mailbox m;struct wr_iot_control_result result;
 wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,mailbox_directory,0));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_QUEUED);
 assert(!strcmp(result.id,on.id)&&!faccessat(m.directory,"request",F_OK,0));
 wr_iot_mailbox_close(&m);
 char path[PATH_MAX];const char *names[]={"request","result","lock"};
 for(unsigned i=0;i<3;i++){assert(snprintf(path,sizeof(path),"%s/%s",mailbox_directory,names[i])<(int)sizeof(path));assert(!unlink(path));}
 assert(!rmdir(mailbox_directory));
}
'''
header=(here/'rc-shutdown-admission.h').read_text()
a=' wr_iot_rc_shutdown.active=1;';assert header.count(a)==1
header=header.replace(a,' admission_before_publish();\n'+a,1)
a='  wr_iot_rc_shutdown.active=0;\n  wr_iot_rc_shutdown.pending=0;'
# Old source lacks this rejection path: the queued-shutdown assertion must fail.
if a in header:header=header.replace(a,'  admission_duplicate();\n'+a,1)
with tempfile.TemporaryDirectory(prefix='wr-admission-window-') as d:
 p=Path(d);(p/'admission-under-test.h').write_text(header)
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 (p/'check.c').write_text(pre+ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body+main)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p/'check.c'),*[str(here/n) for n in units],'-o',str(p/'check')],check=True)
 for mode in (1,2):
  for sig in (0,1):subprocess.run([str(p/'check'),d,str(mode),str(sig)],check=True,timeout=15)
print('PASS real TERM/QUIT at admission publication: actual RC dispatch refuses before mailbox claim/resources; queued request/backend preserved, duplicate pending signal cannot strand admission; driver/resource actors')
