#define _GNU_SOURCE
#include "action-drain.h"
#include "action-send.h"
#include "action-json.h"
#include <assert.h>
#include <sys/file.h>
int main(void){
 int pair[2],one=1,i;struct wr_action_log log={0};struct wr_action_event e={0};
 assert(!socketpair(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK,0,pair));
 assert(!setsockopt(pair[1],SOL_SOCKET,SO_PASSCRED,&one,sizeof(one)));
 e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_INTENT;
 for(i=0;i<20;i++)assert(wr_action_send(pair[0],&e));
 wr_action_drain(&log,pair[1],"/nonexistent-wr-lock","/nonexistent-wr-daemon","/proc",0);
 assert(!log.owner_available&&!log.count&&log.rejected==16);
 wr_action_drain(&log,pair[1],"/nonexistent-wr-lock","/nonexistent-wr-daemon","/proc",0);
 assert(log.rejected==20&&!log.count);
 {
 char temporary[]="/tmp/wr-action-drain-XXXXXX",pid[32];int fd=mkstemp(temporary);unsigned sequence;
 assert(fd>=0);assert(!fchmod(fd,0600));assert(!flock(fd,LOCK_EX|LOCK_NB));
 snprintf(pid,sizeof(pid),"%ld\n",(long)getpid());assert(write(fd,pid,strlen(pid))==(ssize_t)strlen(pid));
 for(sequence=1;sequence<=260;sequence++){
  e.sequence=sequence;assert(wr_action_send(pair[0],&e));
  wr_action_drain_owned(&log,pair[1],temporary,"/proc/self/exe","/proc",geteuid(),0);
 }
 assert(log.owner_available&&log.count==256&&log.dropped==4&&log.events[log.first].sequence==5);
 assert(wr_action_send(pair[0],&e));wr_action_drain_owned(&log,pair[1],temporary,"/proc/self/exe","/proc",geteuid(),0);
 assert(log.rejected==21&&log.count==256);
 assert(!flock(fd,LOCK_UN));e.sequence=261;assert(wr_action_send(pair[0],&e));
 wr_action_drain_owned(&log,pair[1],temporary,"/proc/self/exe","/proc",geteuid(),0);
 assert(!log.owner_available&&log.rejected==22&&log.session.sequence==260);
 assert(log.gap&&log.interruptions==2&&log.count==256);
 wr_action_drain_owned(&log,pair[1],temporary,"/proc/self/exe","/proc",geteuid(),0);assert(log.interruptions==2);
 assert(!flock(fd,LOCK_EX|LOCK_NB));e.sequence=262;assert(wr_action_send(pair[0],&e));
 wr_action_drain_owned(&log,pair[1],temporary,"/proc/self/exe","/proc",geteuid(),0);
 assert(log.owner_available&&!log.gap&&log.interruptions==2&&log.session.missing==1&&log.session.sequence==262&&log.count==256&&log.dropped==5);

 close(fd);unlink(temporary);
 }
 {char json[131072],tiny[2];size_t length;assert(wr_action_json(&log,json,sizeof(json),&length));assert(strstr(json,"\"outcome\":\"unknown\""));assert(strstr(json,"\"dropped\":\"5\""));assert(!wr_action_json(&log,tiny,sizeof(tiny),&length)&&!length);}
 close(pair[0]);close(pair[1]);
 puts("PASS actual owned process receipt, bounded drain, ring overflow, replay and stopped-owner rejection");return 0;
}
