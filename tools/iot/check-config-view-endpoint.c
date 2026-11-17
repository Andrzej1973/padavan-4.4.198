#define _GNU_SOURCE
#include "config-view-endpoint.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <poll.h>
static int scenario,captures;
static char socket_path[108];
static int capture(unsigned int lifetime,struct wr_iot_config_view *view,char revision[33])
{
 assert(lifetime==30);captures++;
 if(scenario==2)return 0;
 memset(view,0,sizeof(*view));memset(revision,'a',32);revision[32]=0;
 if(scenario!=1){
  view->enabled=1;view->key_present=1;strcpy(view->ssid,"IoT");
  strcpy(view->gateway,"192.168.50.1");strcpy(view->mask,"255.255.255.0");
  strcpy(view->first,"192.168.50.20");strcpy(view->last,"192.168.50.200");
 }
 if(scenario==3){
  assert(!unlink(socket_path));int file=open(socket_path,O_CREAT|O_EXCL|O_WRONLY,0600);
  assert(file>=0&&write(file,"foreign",7)==7&&!close(file));
 }
 return 1;
}
int main(void)
{
 for(scenario=0;scenario<4;scenario++){
  char directory[]="/tmp/wr-view-endpoint-XXXXXX";int ready[2],done[2];pid_t child;
  assert(mkdtemp(directory)&&!chmod(directory,0700));
  assert(snprintf(socket_path,sizeof(socket_path),"%s/status.sock",directory)<(int)sizeof(socket_path));
  assert(!pipe(ready)&&!pipe(done));child=fork();assert(child>=0);
  if(!child){
   struct wr_iot_status_endpoint endpoint;char signal='R';int answered=0;
   close(ready[0]);close(done[1]);wr_iot_status_endpoint_init(&endpoint);
   assert(wr_iot_status_endpoint_listen(&endpoint,directory,getuid()));
   assert(write(ready[1],&signal,1)==1);close(ready[1]);
   for(int iteration=0;iteration<400&&!answered;iteration++){
    struct pollfd event={wr_iot_status_endpoint_ready_fd(&endpoint),POLLIN,0};
    assert(poll(&event,1,5)>=0);
    answered=wr_iot_config_view_endpoint_step(&endpoint,30,capture);
   }
   assert(answered&&captures==1&&read(done[0],&signal,1)==1);close(done[0]);
   assert(wr_iot_status_endpoint_close(&endpoint)==(scenario!=3));_exit(0);
  }
  close(ready[1]);close(done[0]);char signal;
  assert(read(ready[0],&signal,1)==1);close(ready[0]);
  struct wr_iot_config_view view,before;char revision[33],old[33];
  memset(&view,0x5a,sizeof(view));before=view;memset(revision,'x',33);memcpy(old,revision,33);
  int ok=wr_iot_config_view_endpoint_query(directory,child,getuid(),&view,revision);
  if(scenario==0)assert(ok&&view.enabled&&view.key_present&&!strcmp(view.ssid,"IoT"));
  else if(scenario==1)assert(ok&&!view.enabled&&!view.key_present&&!view.ssid[0]);
  else assert(!ok&&!memcmp(&view,&before,sizeof(view))&&!memcmp(revision,old,33));
  assert(write(done[1],"D",1)==1);close(done[1]);
  int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
  if(scenario==3){struct stat named;assert(!lstat(socket_path,&named)&&S_ISREG(named.st_mode)&&named.st_size==7);assert(!unlink(socket_path));}
  assert(!rmdir(directory));
 }
 puts("PASS private view endpoint: actual fork/path/socket/nonce exchange, configured/absent/refused views, replacement after capture refuses outputs and preserves foreign file; status lifecycle reused, RC/HTTP scheduling pending");
 return 0;
}
