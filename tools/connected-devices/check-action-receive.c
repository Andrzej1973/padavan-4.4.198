#define _GNU_SOURCE
#include "action-receive.h"
#include <assert.h>
#include <stdio.h>
int main(void){int pair[2],enabled=1;struct wr_action_event e={0},out={0};unsigned char packet[49];
 assert(!socketpair(AF_UNIX,SOCK_DGRAM,0,pair));assert(!setsockopt(pair[1],SOL_SOCKET,SO_PASSCRED,&enabled,sizeof(enabled)));
 e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_IOCTL_ACCEPTED;
 assert(wr_action_encode(&e,packet,48));assert(wr_action_receive(pair[1],getpid(),geteuid(),&out)==0);
 assert(send(pair[0],packet,48,0)==48);assert(wr_action_receive(pair[1],getpid(),geteuid(),&out)==1);assert(out.sequence==1);
 out.sequence=99;assert(send(pair[0],packet,48,0)==48);assert(wr_action_receive(pair[1],getpid()+1,geteuid(),&out)==-1&&out.sequence==99);
 assert(send(pair[0],packet,48,0)==48);assert(wr_action_receive(pair[1],getpid(),geteuid()+1,&out)==-1&&out.sequence==99);
 packet[48]=0;assert(send(pair[0],packet,49,0)==49);assert(wr_action_receive(pair[1],getpid(),geteuid(),&out)==-1&&out.sequence==99);
 assert(!close(pair[0]));assert(!close(pair[1]));puts("PASS kernel peer credentials, nonblocking empty read, foreign PID/UID and truncated datagram rejection");return 0;}
