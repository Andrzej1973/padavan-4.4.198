#define _GNU_SOURCE
#include "action-send.h"
#include "action-receive.h"
#include <assert.h>
#include <stdio.h>
int main(void){int pair[2],enabled=1,buffer=1024,full=0;unsigned int i;struct wr_action_event e={0},out;
 assert(!socketpair(AF_UNIX,SOCK_DGRAM,0,pair));assert(!setsockopt(pair[1],SOL_SOCKET,SO_PASSCRED,&enabled,sizeof(enabled)));assert(!setsockopt(pair[0],SOL_SOCKET,SO_SNDBUF,&buffer,sizeof(buffer)));
 e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_IOCTL_FAILED;e.result=-5;
 errno=EIO;assert(wr_action_send(pair[0],&e)&&errno==EIO);assert(wr_action_receive(pair[1],getpid(),geteuid(),&out)==1&&out.result==-5);
 errno=EINVAL;assert(!wr_action_send(-1,&e)&&errno==EINVAL);
 for(i=0;i<1024;i++){errno=EIO;if(!wr_action_send(pair[0],&e)){full=1;assert(errno==EIO);break;}}
 assert(full);close(pair[1]);errno=EIO;assert(!wr_action_send(pair[0],&e)&&errno==EIO);close(pair[0]);
 puts("PASS nonblocking action send, full/missing receiver and command errno preservation");return 0;}
