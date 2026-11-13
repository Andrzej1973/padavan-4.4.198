#include <signal.h>
#include <string.h>
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
static pid_t fence_owner;
static unsigned fence_depth;
static sigset_t saved_mask;
int wr_iot_radio_stop_fence_begin(struct wr_iot_radio_stop_fence *s)
{
 sigset_t blocked,previous;
 if(!s||s->owner||s->level)return 0;
 if(fence_depth){
  if(fence_owner!=getpid()||!wr_iot_rc_shutdown.active||
     wr_iot_rc_shutdown.pending||fence_depth==~0U)return 0;
  s->owner=getpid();s->level=++fence_depth;return 1;
 }
 sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);
#ifdef SIGQUIT
 sigaddset(&blocked,SIGQUIT);
#endif
 if(sigprocmask(SIG_BLOCK,&blocked,&previous))return 0;
 if(!wr_iot_rc_shutdown_begin()){
  (void)sigprocmask(SIG_SETMASK,&previous,NULL);return 0;
 }
 saved_mask=previous;fence_owner=getpid();fence_depth=1;
 s->owner=getpid();s->level=1;return 1;
}
int wr_iot_radio_stop_fence_end(struct wr_iot_radio_stop_fence *s)
{
 int pending;
 if(!s||s->owner!=getpid()||fence_owner!=getpid()||
    !s->level||s->level!=fence_depth||!wr_iot_rc_shutdown.active)return 0;
 if(fence_depth>1){--fence_depth;memset(s,0,sizeof(*s));return 1;}
 /* Unmask while admission is still active: a queued normal shutdown records
  * its signal instead of tearing down the caller before balanced cleanup. */
 if(sigprocmask(SIG_SETMASK,&saved_mask,NULL))return 0;
 pending=wr_iot_rc_shutdown_end();
 fence_depth=0;fence_owner=0;memset(s,0,sizeof(*s));
 if(pending)raise(pending);
 return 1;
}
