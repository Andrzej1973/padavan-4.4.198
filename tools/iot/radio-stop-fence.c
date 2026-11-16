#include <signal.h>
#include <string.h>
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
static pid_t fence_owner;
static unsigned fence_depth;
static int fence_finishing;
static sigset_t saved_mask;
static int fence_begin(struct wr_iot_radio_stop_fence *s,int routed)
{
 sigset_t blocked,previous;
 if(!s||s->owner||s->level||fence_finishing)return 0;
 if(fence_depth){
  if(routed)return 0; /* A routed request has exactly one outer owner. */
  if(fence_owner!=getpid()||!wr_iot_rc_shutdown.active||
     wr_iot_rc_shutdown.pending||fence_depth==~0U)return 0;
  s->owner=getpid();s->level=++fence_depth;return 1;
 }
 sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);
#ifdef SIGQUIT
 sigaddset(&blocked,SIGQUIT);
#endif
 if(sigprocmask(SIG_BLOCK,&blocked,&previous))return 0;
 if(routed){
  int requested=wr_iot_rc_shutdown.normal_route_requested;
  /* Claim under the blocked mask. Preserve the original route witness until
   * a separate consumer proves physical completion and performs final replay. */
  if(!wr_iot_rc_shutdown.normal_route_armed||wr_iot_rc_shutdown.active||
     wr_iot_rc_shutdown.pending||(requested!=SIGTERM
#ifdef SIGQUIT
     &&requested!=SIGQUIT
#endif
     )){
   (void)sigprocmask(SIG_SETMASK,&previous,NULL);return 0;
  }
  wr_iot_rc_shutdown.active=1;
  wr_iot_rc_shutdown.pending=requested;
 }else if(!wr_iot_rc_shutdown_begin()){
  (void)sigprocmask(SIG_SETMASK,&previous,NULL);return 0;
 }
 saved_mask=previous;fence_owner=getpid();fence_depth=1;
 s->owner=getpid();s->level=1;return 1;
}
int wr_iot_radio_stop_fence_begin(struct wr_iot_radio_stop_fence *s)
{return fence_begin(s,0);}
int wr_iot_radio_stop_fence_begin_routed_shutdown(struct wr_iot_radio_stop_fence *s)
{return fence_begin(s,1);}
static int fence_end(struct wr_iot_radio_stop_fence *s,void (*cleanup)(void *),void *context,int defer_shutdown)
{
 int pending;sigset_t blocked;
 if(fence_finishing||!s||s->owner!=getpid()||fence_owner!=getpid()||
    !s->level||s->level!=fence_depth||!wr_iot_rc_shutdown.active)return 0;
 if(cleanup&&fence_depth!=1)return 0;
 if(fence_depth>1){--fence_depth;memset(s,0,sizeof(*s));return 1;}
 /* Unmask while admission is still active: a queued normal shutdown records
  * its signal instead of tearing down the caller before balanced cleanup. */
 fence_finishing=1;
 if(sigprocmask(SIG_SETMASK,&saved_mask,NULL)){fence_finishing=0;return 0;}
 if(defer_shutdown&&wr_iot_rc_shutdown.pending){
  /* The handler has recorded the intent while admission is still active.
   * Re-block for owned shutdown continuation; even re-block failure retains
   * admission/token and never grants permission to clean up or replay. */
  sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);
#ifdef SIGQUIT
  sigaddset(&blocked,SIGQUIT);
#endif
  (void)sigprocmask(SIG_BLOCK,&blocked,NULL);fence_finishing=0;return 0;
 }
 if(cleanup)cleanup(context);
 pending=wr_iot_rc_shutdown_end();
 fence_depth=0;fence_owner=0;memset(s,0,sizeof(*s));fence_finishing=0;
 if(pending)raise(pending);
 return 1;
}

int wr_iot_radio_stop_fence_end(struct wr_iot_radio_stop_fence *s)
{return fence_end(s,NULL,NULL,0);}
int wr_iot_radio_stop_fence_end_cleanup(struct wr_iot_radio_stop_fence *s,
 void (*cleanup)(void *),void *context)
{return cleanup?fence_end(s,cleanup,context,0):0;}

int wr_iot_radio_stop_fence_end_cleanup_unless_shutdown(struct wr_iot_radio_stop_fence *s,
 void (*cleanup)(void *),void *context)
{return cleanup?fence_end(s,cleanup,context,1):0;}
