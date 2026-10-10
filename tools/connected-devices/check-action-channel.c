#define _GNU_SOURCE
#include "action-channel.h"
#include "action-endpoint.h"
#include "action-receive.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
int main(void){char dir[]="/tmp/action-channel-XXXXXX",path[108],lock[114];struct wr_action_channel c;struct wr_action_endpoint server;struct wr_action_event e={0},out;
 assert(mkdtemp(dir));assert(!chmod(dir,0700));snprintf(path,sizeof(path),"%s/events",dir);snprintf(lock,sizeof(lock),"%s.lock",path);wr_action_channel_init(&c);
 e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_INTENT;
 errno=EIO;assert(!wr_action_channel_emit(&c,path,0,&e)&&errno==EIO);assert(!wr_action_endpoint_open(&server,path));assert(!wr_action_channel_emit(&c,path,9999,&e));assert(wr_action_channel_emit(&c,path,10000,&e));assert(wr_action_receive(server.fd,getpid(),geteuid(),&out)==1);
 wr_action_endpoint_close(&server);assert(!wr_action_channel_emit(&c,path,11000,&e));assert(!wr_action_endpoint_open(&server,path));assert(!wr_action_channel_emit(&c,path,19999,&e));assert(wr_action_channel_emit(&c,path,20000,&e));assert(wr_action_receive(server.fd,getpid(),geteuid(),&out)==1);
 wr_action_channel_close(&c);wr_action_endpoint_close(&server);assert(!unlink(lock));assert(!rmdir(dir));puts("PASS bounded reconnect after missing/restarted collector and errno isolation");return 0;}
