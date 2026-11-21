from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-rc-runtime.c').read_text().split('int main(void)')[0]
for line in ('static char directory[]="/tmp/iot-rc-runtime-XXXXXX";\n','#define WR_IOT_CONTROL_DIRECTORY directory\n'):
 assert prefix.count(line)==1
 prefix=prefix.replace(line,'',1)
body=r'''
#include "config-view-runtime.h"
#include "config-view-endpoint.h"
#include <sys/socket.h>
#include <sys/un.h>
static int edit_ready,captures;
int wr_iot_rc_edit_backend_ready(void){return edit_ready;}
int wr_iot_rc_edit_view(unsigned int lifetime,struct wr_iot_config_view *view,char revision[33])
{
 assert(lifetime==120);captures++;memset(view,0,sizeof(*view));
 memset(revision,'b',32);revision[32]=0;return 1;
}
int main(int argc,char **argv)
{
 const char *directory=WR_IOT_CONTROL_DIRECTORY;
 sigset_t empty;struct sigaction action={0};struct stat named;int status;
 int mode=argc>1?atoi(argv[1]):0;
 assert(!mkdir(directory,mode==1?0755:0700));
 if(mode==1)assert(!chmod(directory,0755));
 if(mode==2){
  assert(!mkdir(WR_IOT_CONFIG_VIEW_DIRECTORY,0700));
  int file=open(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock",O_CREAT|O_EXCL|O_WRONLY,0600);
  assert(file>=0&&write(file,"foreign",7)==7&&!close(file));
 }
 sigemptyset(&empty);action.sa_handler=handler;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGUSR1,&action,NULL));
 assert(!wr_iot_rc_view_runtime_install());edit_ready=1;
 assert(wr_iot_rc_view_runtime_install()&&!wr_iot_rc_view_runtime_install());
 notification=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(!initialized);notification=0;
 pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 if(mode==1){
  assert(lstat(WR_IOT_CONFIG_VIEW_DIRECTORY,&named));
  assert(!chmod(directory,0700));
 }
 if(mode==2){
  for(int index=0;index<3;index++)wr_iot_rc_wait(&empty,&notification,&alarm_flag);
  assert(!lstat(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock",&named)&&S_ISREG(named.st_mode)&&named.st_size==7&&!captures);
  assert(!wr_iot_rc_view_runtime_close());
 }else{
  int available=0;
  for(int index=0;index<30&&!available;index++){
   available=!lstat(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock",&named)&&S_ISSOCK(named.st_mode);
   if(!available)wr_iot_rc_wait(&empty,&notification,&alarm_flag);
  }
  assert(available);pending=0;
  pid_t child=fork();assert(child>=0);
  if(!child){
   struct wr_iot_config_view view;char revision[33];
   assert(!wr_iot_rc_view_runtime_close()&&!view_bound());
   assert(wr_iot_config_view_endpoint_query(WR_IOT_CONFIG_VIEW_DIRECTORY,getppid(),getuid(),&view,revision));
   assert(!view.enabled&&!view.key_present&&!view.ssid[0]);_exit(0);
  }
  for(int index=0;index<4&&!captures;index++)wr_iot_rc_wait(&empty,&notification,&alarm_flag);
  assert(captures==1&&waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
  if(mode==3){
   assert(!rename(directory,WR_IOT_CONTROL_DIRECTORY "-old"));
   assert(!symlink(WR_IOT_CONTROL_DIRECTORY "-old",directory));
  }else{
   assert(!unlink(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock"));
   int file=open(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock",O_CREAT|O_EXCL|O_WRONLY,0600);
   assert(file>=0&&write(file,"foreign",7)==7&&!close(file));
  }
  pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
  assert(!wr_iot_rc_view_runtime_close());
  if(mode==3)assert(!lstat(directory,&named)&&S_ISLNK(named.st_mode));
  else assert(!lstat(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock",&named)&&S_ISREG(named.st_mode)&&named.st_size==7);
 }
 if(mode==3){
  assert(!wr_iot_status_endpoint_close(&endpoint));
  assert(!unlink(directory));
  assert(lstat(WR_IOT_CONTROL_DIRECTORY "-old/view/status.sock",&named));
  assert(!rmdir(WR_IOT_CONTROL_DIRECTORY "-old/view"));
  assert(!unlink(WR_IOT_CONTROL_DIRECTORY "-old/status.sock")&&!unlink(WR_IOT_CONTROL_DIRECTORY "-old/lock"));
  assert(!rmdir(WR_IOT_CONTROL_DIRECTORY "-old"));return 0;
 }
 assert(!unlink(WR_IOT_CONFIG_VIEW_DIRECTORY "/status.sock")&&!rmdir(WR_IOT_CONFIG_VIEW_DIRECTORY));
 assert(wr_iot_status_endpoint_close(&endpoint));char path[256];
 assert(snprintf(path,sizeof(path),"%s/lock",directory)<(int)sizeof(path));assert(!unlink(path)&&!rmdir(directory));
 puts("PASS actual RC view service: explicit backend/readiness gate, private parent/child ownership, bounded retry after repair, real child query, foreign socket preservation and copied-owner refusal; capture actor, no startup/HTTP binding");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-view-service-') as directory:
 root=Path(directory);source=root/'check.c';source.write_text(prefix+body);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
  '-DWR_IOT_CONTROL_DIRECTORY="'+str(root/'control')+'"','-DWR_IOT_VIEW_RUNTIME_UID=geteuid()',
  str(source),*[str(here/name) for name in ('control-mailbox.c','status-endpoint.c','status-channel.c','config-view-endpoint.c','config-view-channel.c','config-view-runtime.c')],
  '-o',str(binary)],check=True)
 for mode in range(4):subprocess.run([str(binary),str(mode)],check=True,timeout=15)
