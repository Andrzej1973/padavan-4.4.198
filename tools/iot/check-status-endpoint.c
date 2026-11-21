#define _GNU_SOURCE
#include "status-endpoint.h"
#include <assert.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <poll.h>
#include <time.h>
static int observed;
static int observe(const struct wr_iot_control_result *r){assert(r->created&&r->state==WR_IOT_RESULT_APPLIED);observed++;return 1;}
int main(void)
{
 char directory[]="/tmp/iot-status-endpoint-XXXXXX",path[256];assert(mkdtemp(directory));
 assert(snprintf(path,sizeof(path),"%s/status.sock",directory)<(int)sizeof(path));
 struct wr_iot_status_endpoint endpoint;wr_iot_status_endpoint_init(&endpoint);
 int file=open(path,O_CREAT|O_EXCL|O_WRONLY,0600);assert(file>=0);close(file);
 assert(!wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
 struct stat st;assert(!lstat(path,&st)&&S_ISREG(st.st_mode));assert(!unlink(path));
 assert(!chmod(directory,0755));assert(!wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));assert(!chmod(directory,0700));
 int pipefd[2];assert(!pipe(pipefd));pid_t child=fork();assert(child>=0);
 if(!child){
  close(pipefd[0]);assert(wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
  assert(!lstat(path,&st)&&S_ISSOCK(st.st_mode)&&(st.st_mode&0777)==0600);
  struct wr_iot_status_endpoint duplicate;wr_iot_status_endpoint_init(&duplicate);
  assert(!wr_iot_status_endpoint_listen(&duplicate,directory,geteuid()));
  assert(write(pipefd[1],"R",1)==1);close(pipefd[1]);
  struct pollfd p={endpoint.listener,POLLIN,0};assert(poll(&p,1,2000)==1);
  int answered=wr_iot_status_endpoint_step(&endpoint,observe);
  if(!answered){assert(endpoint.connection>=0);p.fd=endpoint.connection;assert(poll(&p,1,2000)==1);answered=wr_iot_status_endpoint_step(&endpoint,observe);}
  assert(answered&&observed==1&&endpoint.connection==-1);
  /* Parent still needs to validate the bound path after receiving reply. */
  _exit(0);
 }
 close(pipefd[1]);char byte;assert(read(pipefd[0],&byte,1)==1);close(pipefd[0]);
 struct timespec now;assert(!clock_gettime(CLOCK_MONOTONIC,&now));
 struct wr_iot_control_result result={.id="01010101010101010101010101010101",.created=(unsigned long long)now.tv_sec,.observed=(unsigned long long)now.tv_sec,.state=WR_IOT_RESULT_APPLIED};
 assert(wr_iot_status_endpoint_query(directory,child,geteuid(),&result));
 int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 /* Child exit intentionally leaves socket: a fresh listener must refuse it. */
 assert(!wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));assert(!unlink(path));
 assert(wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
 pid_t other=fork();assert(other>=0);
 if(!other){assert(!wr_iot_status_endpoint_close(&endpoint));_exit(0);}
 assert(waitpid(other,&status,0)==other&&WIFEXITED(status)&&!WEXITSTATUS(status));
 assert(!lstat(path,&st));assert(wr_iot_status_endpoint_close(&endpoint));
 assert(lstat(path,&st));
 assert(wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
 int idle=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(idle>=0);
 struct sockaddr_un address={.sun_family=AF_UNIX};strcpy(address.sun_path,path);
 assert(!connect(idle,(struct sockaddr *)&address,sizeof(address)));
 assert(!wr_iot_status_endpoint_step(&endpoint,observe)&&endpoint.connection>=0);
 endpoint.expires=1;assert(!wr_iot_status_endpoint_step(&endpoint,observe)&&endpoint.connection==-1);
 close(idle);
 assert(!unlink(path));file=open(path,O_CREAT|O_EXCL|O_WRONLY,0600);assert(file>=0);
 assert(write(file,"foreign",7)==7);close(file);
 assert(!wr_iot_status_endpoint_close(&endpoint));
 assert(!lstat(path,&st)&&S_ISREG(st.st_mode)&&st.st_size==7);
 assert(!unlink(path));
 assert(wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
 int slot=endpoint.listener;assert(!close(slot));
 file=open("/dev/null",O_RDONLY);assert(file>=0);
 if(file!=slot){assert(dup2(file,slot)==slot);assert(!close(file));}
 assert(wr_iot_status_endpoint_ready_fd(&endpoint)==-1);
 assert(wr_iot_status_endpoint_close(&endpoint));
 assert(fcntl(slot,F_GETFD)>=0);assert(!close(slot));
 assert(wr_iot_status_endpoint_listen(&endpoint,directory,geteuid()));
 idle=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(idle>=0);
 assert(!connect(idle,(struct sockaddr *)&address,sizeof(address)));
 assert(!wr_iot_status_endpoint_step(&endpoint,observe)&&endpoint.connection>=0);
 slot=endpoint.connection;assert(!close(slot));file=open("/dev/null",O_RDONLY);assert(file>=0);
 if(file!=slot){assert(dup2(file,slot)==slot);assert(!close(file));}
 assert(wr_iot_status_endpoint_ready_fd(&endpoint)==endpoint.listener&&endpoint.connection==-1);
 assert(wr_iot_status_endpoint_close(&endpoint));assert(fcntl(slot,F_GETFD)>=0);
 assert(!close(slot)&&!close(idle)&&!rmdir(directory));
 puts("PASS private status endpoint: real fork request, private directory/socket mode, duplicate/stale/foreign file refusal, child cannot unlink parent endpoint, owned cleanup, bounded idle client and foreign replacement and reused descriptors retained; RC scheduling not installed");
}
