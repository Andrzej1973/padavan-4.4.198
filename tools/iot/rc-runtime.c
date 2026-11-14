#define _GNU_SOURCE
#include <signal.h>
#include <poll.h>
#include <time.h>
#include <unistd.h>
#include "rc-runtime.h"
#include "control-channel.h"
#include "rc-backend.h"
#include "rc-physical-stop.h"
#include "status-endpoint.h"
#ifndef WR_IOT_RUNTIME_UID
#define WR_IOT_RUNTIME_UID 0
#endif
static struct wr_iot_status_endpoint endpoint;
static int initialized,listening,disabled;
static unsigned long long next_init;
static unsigned long long next_progress;
static unsigned long long runtime_ms(void)
{struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)||t.tv_sec<=0)return 0;return (unsigned long long)t.tv_sec*1000+(unsigned long long)t.tv_nsec/1000000;}
static void runtime_init(void)
{
 struct wr_iot_mailbox m;unsigned long long now=runtime_ms();
 if(listening||disabled)return;
 if(!initialized){initialized=1;wr_iot_status_endpoint_init(&endpoint);}
 if(geteuid()!=WR_IOT_RUNTIME_UID){disabled=1;return;}
 if(!now||(next_init&&now<next_init))return;
 /* A transient filesystem/socket error must not disable status forever.
  * Keep retries bounded; existing foreign endpoints remain untouched. */
 next_init=now+1000;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,1))return;
 wr_iot_mailbox_close(&m);
 listening=wr_iot_status_endpoint_listen(&endpoint,WR_IOT_CONTROL_DIRECTORY,WR_IOT_RUNTIME_UID);
}

void wr_iot_rc_wait(const sigset_t *wait_mask,const volatile int *notification,
 const volatile int *alarm)
{
 sigset_t blocked,previous;struct pollfd p;struct timespec delay,*timeout=NULL;
 unsigned long long now;int pending,fd;
 if(!wait_mask||!notification||!alarm)return;
 sigemptyset(&blocked);sigaddset(&blocked,SIGUSR1);sigaddset(&blocked,SIGALRM);
 /* Atomic flag-check/wait transition: pending signals are delivered by ppoll
  * under the vendor's supplied wait mask, not lost between test and sleep. */
 if(sigprocmask(SIG_BLOCK,&blocked,&previous))return;
 if(*notification||*alarm)goto done;
 runtime_init();pending=wr_iot_rc_pending()||wr_iot_rc_physical_pending();now=runtime_ms();
 fd=wr_iot_status_endpoint_ready_fd(&endpoint);
 p.fd=fd;p.events=POLLIN;p.revents=0;
 if(pending||endpoint.connection>=0){
  unsigned long long ms=100;
  if(pending&&now&&now>=next_progress)ms=0;
  else if(pending&&now&&next_progress-now<ms)ms=next_progress-now;
  delay.tv_sec=0;delay.tv_nsec=(long)ms*1000000;timeout=&delay;
 }
 if(!listening&&!disabled){
  unsigned long long ms=1000;
  if(now&&next_init>now)ms=next_init-now;
  if(ms>1000)ms=1000;
  if(!timeout||(unsigned long long)delay.tv_nsec/1000000>ms){
   delay.tv_sec=(time_t)(ms/1000);delay.tv_nsec=(long)(ms%1000)*1000000;timeout=&delay;
  }
 }
 (void)ppoll(fd>=0?&p:NULL,fd>=0?1:0,timeout,wait_mask);
 if(*notification||*alarm)goto done;
 (void)wr_iot_status_endpoint_step(&endpoint,wr_iot_rc_backend_observed);
 now=runtime_ms();
 if((wr_iot_rc_pending()||wr_iot_rc_physical_pending())&&now&&now>=next_progress){
  next_progress=now+100;
  if(wr_iot_rc_physical_pending())wr_iot_rc_physical_step();
  else (void)wr_iot_rc_continue();
 }
 done:(void)sigprocmask(SIG_SETMASK,&previous,NULL);
}
