#include <unistd.h>
#include <signal.h>
#include <limits.h>
#include "restart-auth-stop.h"
#include "rc-shutdown-admission.h"
static int admit(unsigned long long now)
{return now&&now<=ULLONG_MAX-3000&&wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;}
int wr_iot_auth_stop_begin(struct wr_iot_auth_stop*s,unsigned long long now)
{
 int present;
 if(!s||s->owner||s->busy||s->phase!=WR_AUTH_IDLE||s->attempted||!admit(now))return 0;
 s->owner=getpid();s->busy=1;s->last=now;s->phase=WR_AUTH_RETAINED;
 present=wr_iot_auth_stop_present();
 if(present==0)s->phase=WR_AUTH_STOPPED;
 else if(present==1){
  s->attempted=1;s->deadline=now+3000;
  /* Mark before invoking: even an uncertain signal is never resubmitted. */
  if(wr_iot_auth_stop_signal(SIGTERM)==1)s->phase=WR_AUTH_TERM_WAIT;
 }
 s->busy=0;return 1;
}
int wr_iot_auth_stop_step(struct wr_iot_auth_stop*s,unsigned long long now)
{
 int present,ready=0;
 if(!s||s->owner!=getpid()||s->busy||!admit(now)||now<s->last)return 0;
 s->last=now;s->busy=1;
 if(s->phase==WR_AUTH_RETAINED)goto done;
 present=wr_iot_auth_stop_present();
 if(present!=0&&present!=1)goto done;
 if(present==0){s->phase=WR_AUTH_STOPPED;ready=1;goto done;}
 if(s->phase==WR_AUTH_STOPPED){s->phase=WR_AUTH_RETAINED;goto done;}
 if(now<s->deadline)goto done;
 if(s->phase==WR_AUTH_TERM_WAIT&&s->attempted==1){
  s->attempted|=2;s->phase=WR_AUTH_RETAINED;s->deadline=now+1000;
  if(wr_iot_auth_stop_signal(SIGKILL)==1)s->phase=WR_AUTH_KILL_WAIT;
 }else if(s->phase==WR_AUTH_KILL_WAIT)s->phase=WR_AUTH_RETAINED;
 done:s->busy=0;return ready;
}
