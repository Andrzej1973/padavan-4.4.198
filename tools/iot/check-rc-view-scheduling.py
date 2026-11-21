from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-rc-runtime.c').read_text().split('int main(void)')[0]
body=r'''
#include "config-view-endpoint.h"
#include <sys/socket.h>
#include <sys/un.h>
static struct wr_iot_status_endpoint view_endpoint;
static char view_directory[]="/tmp/wr-rc-view-XXXXXX";
static int view_listening,view_inits,view_steps,view_captures;
static int capture_view(unsigned int lifetime,struct wr_iot_config_view *out,char revision[33])
{
 assert(lifetime==30);view_captures++;memset(out,0,sizeof(*out));
 memset(revision,'a',32);revision[32]=0;return 1;
}
static void init_view(void)
{
 view_inits++;
 if(!view_listening)view_listening=wr_iot_status_endpoint_listen(&view_endpoint,view_directory,getuid());
}
static int view_fd(void){return wr_iot_status_endpoint_ready_fd(&view_endpoint);}
static unsigned int view_delay(void){return !view_listening?1000:view_endpoint.connection>=0?100:0;}
static void step_view(void){view_steps++;(void)wr_iot_config_view_endpoint_step(&view_endpoint,30,capture_view);}
int main(void)
{
 struct wr_iot_rc_view_hooks hooks={init_view,view_fd,view_delay,step_view},bad=hooks;
 sigset_t empty,blocked,old;struct sigaction action={0};int status;
 assert(mkdtemp(directory)&&mkdtemp(view_directory));wr_iot_status_endpoint_init(&view_endpoint);
 sigemptyset(&empty);sigemptyset(&blocked);sigaddset(&blocked,SIGUSR1);
 action.sa_handler=handler;sigemptyset(&action.sa_mask);assert(!sigaction(SIGUSR1,&action,NULL));
 bad.step=NULL;assert(!wr_iot_rc_runtime_register_view(&bad));
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_rc_runtime_register_view(&hooks));wr_iot_rc_shutdown.active=0;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_rc_runtime_register_view(&hooks));wr_iot_rc_shutdown.pending=0;
 wr_iot_rc_shutdown.radio_on_owned=1;assert(!wr_iot_rc_runtime_register_view(&hooks));wr_iot_rc_shutdown.radio_on_owned=0;
 assert(wr_iot_rc_runtime_register_view(&hooks));assert(!wr_iot_rc_runtime_register_view(&hooks));
 hooks.step=NULL;assert(view_hooks.step==step_view);
 notification=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(!initialized&&!view_inits&&!view_steps);notification=0;
 pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(listening&&view_listening&&steps==1&&view_inits==1&&!view_captures);pending=0;
 pid_t child=fork();assert(child>=0);
 if(!child){
  struct wr_iot_config_view view;char revision[33];
  assert(!view_bound()&&!wr_iot_status_endpoint_close(&view_endpoint));
  assert(wr_iot_config_view_endpoint_query(view_directory,getppid(),getuid(),&view,revision));
  assert(!view.enabled&&!view.key_present&&strlen(revision)==32);_exit(0);
 }
 for(int iteration=0;iteration<4&&!view_captures;iteration++)wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(view_captures==1&&steps==1&&waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 assert(!sigprocmask(SIG_BLOCK,&blocked,&old));child=fork();assert(child>=0);
 if(!child){assert(!kill(getppid(),SIGUSR1));_exit(0);}
 int before_steps=view_steps;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(notification&&view_steps==before_steps&&steps==1);
 assert(!sigprocmask(SIG_SETMASK,&old,NULL));
 assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));notification=0;
 int idle=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(idle>=0);
 struct sockaddr_un address={.sun_family=AF_UNIX};
 assert(snprintf(address.sun_path,sizeof(address.sun_path),"%s/status.sock",view_directory)<(int)sizeof(address.sun_path));
 assert(!connect(idle,(struct sockaddr *)&address,sizeof(address)));
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(view_endpoint.connection>=0);
 view_endpoint.expires=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(view_endpoint.connection==-1&&view_captures==1&&steps==1);close(idle);
 assert(wr_iot_status_endpoint_close(&view_endpoint)&&!rmdir(view_directory));
 assert(wr_iot_status_endpoint_close(&endpoint));char path[256];
 assert(snprintf(path,sizeof(path),"%s/lock",directory)<(int)sizeof(path));assert(!unlink(path)&&!rmdir(directory));
 puts("PASS actual RC dual-endpoint ppoll: once-only PID-bound registration, request/notification priority, real view exchange, signal wake skips view work, idle client timer and old continuation cadence; capture actor only");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rc-view-build-') as directory:
 root=Path(directory);source=root/'check.c';binary=root/'check';source.write_text(prefix+body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(source),
  *[str(here/name) for name in ('control-mailbox.c','status-endpoint.c','status-channel.c','config-view-endpoint.c','config-view-channel.c')],
  '-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
