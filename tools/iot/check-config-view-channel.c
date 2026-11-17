#define _GNU_SOURCE
#include "config-view-channel.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <poll.h>
static int scenario,captures;
static int capture(unsigned int lifetime,struct wr_iot_config_view *view,char revision[33])
{
 assert(lifetime==30);captures++;
 memset(view,0,sizeof(*view));memset(revision,'a',32);revision[32]=0;
 if(scenario==1)return 0;
 if(scenario==2)return 1;
 view->enabled=1;view->key_present=1;strcpy(view->ssid,"IoT \"<>\\");
 strcpy(view->gateway,"192.168.50.1");strcpy(view->mask,"255.255.255.0");
 strcpy(view->first,"192.168.50.20");strcpy(view->last,"192.168.50.200");
 if(scenario==3)view->ssid[25]='x';
 if(scenario==4)revision[0]='z';
 return 1;
}
int main(void)
{
 char directory[]="/tmp/wr-view-channel-XXXXXX";struct sockaddr_un address={.sun_family=AF_UNIX};
 assert(mkdtemp(directory));assert(snprintf(address.sun_path,sizeof(address.sun_path),"%s/view",directory)<(int)sizeof(address.sun_path));
 for(scenario=0;scenario<12;scenario++){
  int pipefd[2];pid_t child;assert(!pipe(pipefd));child=fork();assert(child>=0);
  if(!child){
   int listener,connection;char ready='R';struct pollfd event;
   close(pipefd[0]);listener=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(listener>=0);
   assert(!bind(listener,(struct sockaddr *)&address,sizeof(address))&&!listen(listener,1));
   assert(write(pipefd[1],&ready,1)==1);close(pipefd[1]);
   connection=accept(listener,NULL,NULL);assert(connection>=0);close(listener);
   event=(struct pollfd){connection,POLLIN,0};int available=poll(&event,1,1200);
   if(scenario==10||scenario==11){assert(available>=0);}
   else if(scenario>=5){
    unsigned char query[36],reply[169]={0};assert(available==1&&recv(connection,query,sizeof(query),0)==36);
    if(scenario==9){struct pollfd idle={-1,0,0};assert(poll(&idle,0,1100)==0);}
    else{
     memcpy(reply,"WIV1",4);memcpy(reply+4,query+4,32);reply[36]=1;memset(reply+37,'a',32);
     if(scenario==5)reply[4]^=1;
     if(scenario==6)memcpy(reply,"WIC1",4);
     if(scenario==8)reply[69]=2;
     assert(send(connection,reply,scenario==7?169:168,MSG_NOSIGNAL)==(scenario==7?169:168));
    }
   }else{
    assert(available==1&&wr_iot_config_view_serve_once(connection,getuid(),30,capture)&&captures==1);
   }
   close(connection);assert(!unlink(address.sun_path));_exit(0);
  }
  close(pipefd[1]);char ready;assert(read(pipefd[0],&ready,1)==1);close(pipefd[0]);
  int connection=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);assert(connection>=0);
  assert(!connect(connection,(struct sockaddr *)&address,sizeof(address)));
  struct wr_iot_config_view view,before;char revision[33],old[33];
  memset(&view,0x5a,sizeof(view));before=view;memset(revision,'x',33);memcpy(old,revision,33);
  int ok=wr_iot_config_view_query(connection,scenario==10?child+10000:child,
                                scenario==11?getuid()+1:getuid(),&view,revision);
  if(scenario==0)assert(ok&&view.enabled&&view.key_present&&!strcmp(view.ssid,"IoT \"<>\\")&&strlen(revision)==32);
  else if(scenario==2)assert(ok&&!view.enabled&&!view.key_present&&!view.ssid[0]);
  else assert(!ok&&!memcmp(&view,&before,sizeof(view))&&!memcmp(revision,old,33));
  close(connection);int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 }
 for(int invalid=0;invalid<8;invalid++){
  int pair[2];unsigned char query[37]={0};
  assert(!socketpair(AF_UNIX,(invalid==7?SOCK_STREAM:SOCK_SEQPACKET)|SOCK_CLOEXEC,0,pair));
  memcpy(query,"WIQ1",4);memset(query+4,0x5a,32);
  if(invalid==2)memcpy(query,"WIS1",4);
  if(invalid==3)memset(query+4,0,32);
  size_t length=invalid==0?35:invalid==1?37:36;
  assert(send(pair[0],query,length,MSG_NOSIGNAL)==(ssize_t)length);
  assert(!wr_iot_config_view_serve_once(pair[1],invalid==6?getuid()+1:getuid(),
                                      invalid==5?301:30,invalid==4?NULL:capture)&&!captures);
  close(pair[0]);close(pair[1]);
 }
 assert(!rmdir(directory));
 puts("PASS real fork/SEQPACKET view protocol: configured/absent, refusal, zero padding/token/type/nonce/size/flag/timeout/PID/UID gates and unchanged failure outputs; no endpoint or HTTP binding");
 return 0;
}
