#include "steering-action.h"
#include <assert.h>
#include <stdio.h>
static unsigned int calls,count;static int fail,report_fail;static struct wr_action_event events[8];
static int command(enum wr_band_protocol p,const struct wr_band_request *r,void *c){(void)p;(void)r;(void)c;calls++;errno=fail?EIO:0;return fail?-1:0;}
static int emit(const struct wr_action_event *e,void *c){(void)c;events[count++]=*e;errno=EPERM;return !report_fail;}
int main(void){struct wr_action_reporter reporter={1,0,0,emit,NULL};struct wr_band_request r={0};r.mac[0]=2;r.command=WR_ADD;r.cookie=7;
 assert(!wr_action_steering_command(&reporter,0,5000,WR_MT76X3,&r,command,NULL));assert(calls==1&&count==2&&errno==0);assert(events[0].stage==WR_ACTION_INTENT&&events[1].stage==WR_ACTION_IOCTL_ACCEPTED&&events[1].cookie==7);
 fail=report_fail=1;r.command=WR_DELETE;assert(wr_action_steering_command(&reporter,1,6000,WR_MT76X2,&r,command,NULL)==-1);assert(calls==2&&count==4&&errno==EIO&&reporter.dropped==2);assert(events[3].stage==WR_ACTION_IOCTL_FAILED&&events[3].result==-EIO&&events[3].operation==WR_ACTION_REMOVE_CANDIDATE);
 r.command=WR_GRANT_QUERY;assert(wr_action_steering_command(&reporter,1,7000,WR_MT76X2,&r,command,NULL)==-1);assert(calls==3&&count==4);
 puts("PASS exactly-once steering command, intent/result distinction, report failure isolation and query exclusion");return 0;}
