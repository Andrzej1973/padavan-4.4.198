#define _GNU_SOURCE
#include "status-channel.h"
#include <assert.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <unistd.h>
#include <poll.h>
#include <time.h>
static int verdict;
static enum wr_iot_result_state expected_state;
static int observe(const struct wr_iot_control_result *r)
{assert(!strcmp(r->id,"01010101010101010101010101010101")&&r->created&&r->observed&&r->state==expected_state);return verdict;}
int main(void)
{
 char directory[]="/tmp/iot-status-channel-XXXXXX";assert(mkdtemp(directory));
 struct sockaddr_un address={.sun_family=AF_UNIX};
 assert(snprintf(address.sun_path,sizeof(address.sun_path),"%s/status",directory)<(int)sizeof(address.sun_path));
 for(int scenario=0;scenario<17;scenario++){
  expected_state=scenario>=12?WR_IOT_RESULT_SAVED_FLASH:scenario>=10?WR_IOT_RESULT_STORED_RAM:WR_IOT_RESULT_APPLIED;
  int pipefd[2];assert(!pipe(pipefd));pid_t child=fork();assert(child>=0);
  if(!child){
   close(pipefd[0]);int listener=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(listener>=0);
   assert(!bind(listener,(struct sockaddr *)&address,sizeof(address))&&!listen(listener,1));
   assert(write(pipefd[1],"R",1)==1);close(pipefd[1]);
   int connection=accept(listener,NULL,NULL);assert(connection>=0);close(listener);
   struct pollfd p={connection,POLLIN,0};int ready=poll(&p,1,1200);
   if(scenario==2){assert(ready>=0);close(connection);assert(!unlink(address.sun_path));_exit(0);}
   assert(ready==1);
   if((scenario>=4&&scenario<=7)||scenario==11||scenario==13||scenario==14||scenario==15||scenario==16){
    unsigned char query[84],reply[86];assert(recv(connection,query,sizeof(query),0)==84);
    if(scenario==15||scenario==16){
     memcpy(query,scenario==15?"WIC1":"WIS1",4);
     /* A peer may choose a query kind, but observer state derives only from
      * that kind; a retained flash-only receipt cannot satisfy RAM/runtime. */
     memcpy(reply,query,84);reply[84]=0;
     assert(send(connection,reply,85,MSG_NOSIGNAL)==85);
     close(connection);assert(!unlink(address.sun_path));_exit(0);
    }
    memcpy(reply,query,84);reply[84]=1;reply[85]=0;
    if(scenario==4)reply[52]^=1;
    if(scenario==13)memcpy(reply,"WIC1",4);
    if(scenario==14)memcpy(reply,"WIS1",4);
    if(scenario==11)memcpy(reply,"WIS1",4); /* Cross-kind response cannot acknowledge WIC1. */
    if(scenario==7){struct pollfd wait={connection,POLLIN,0};assert(poll(&wait,1,1200)>=0);}
    else {size_t bytes=scenario==5?84:scenario==6?86:85;assert(send(connection,reply,bytes,MSG_NOSIGNAL)==(ssize_t)bytes);}
    close(connection);assert(!unlink(address.sun_path));_exit(0);
   }
   if(scenario==8||scenario==9){assert(!wr_iot_status_serve_once(connection,geteuid(),observe));close(connection);assert(!unlink(address.sun_path));_exit(0);}
   verdict=(scenario==0||scenario==10||scenario==12)?1:scenario==1?0:2;
   assert(wr_iot_status_serve_once(connection,geteuid(),observe));
   close(connection);assert(!unlink(address.sun_path));_exit(0);
  }
  close(pipefd[1]);char c;assert(read(pipefd[0],&c,1)==1);close(pipefd[0]);
  int connection=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(connection>=0);
  assert(!connect(connection,(struct sockaddr *)&address,sizeof(address)));
  struct timespec now;assert(!clock_gettime(CLOCK_MONOTONIC,&now));
  struct wr_iot_control_result r={.id="01010101010101010101010101010101",.created=(unsigned long long)now.tv_sec,.observed=(unsigned long long)now.tv_sec,.state=WR_IOT_RESULT_APPLIED};
  r.state=expected_state;
  if(scenario==8||scenario==9){unsigned char bad[85]={0};size_t bytes=scenario==8?3:sizeof(bad);assert(send(connection,bad,bytes,0)==(ssize_t)bytes);}
  else assert(wr_iot_status_query(connection,scenario==2?child+1000:child,geteuid(),&r)==(scenario==0||scenario==10||scenario==12));
  close(connection);int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
 }
 assert(!rmdir(directory));
 puts("PASS real fork/Unix seqpacket status: typed runtime/RAM/flash queries, cross-kind response refusal, verified PID/UID/nonce/exact success1, wrong peer/corruption/length/timeout/malformed refusal; device acceptance pending");
}
