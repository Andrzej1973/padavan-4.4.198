/* PID 1 IoT transaction signal admission. Signal handler touches only
 * sig_atomic_t fields; process faults retain the stock fatal path. */
#ifndef WR_IOT_RC_SHUTDOWN_ADMISSION_H
#define WR_IOT_RC_SHUTDOWN_ADMISSION_H
#include <signal.h>

struct wr_iot_rc_shutdown_admission {
 volatile sig_atomic_t active;
 volatile sig_atomic_t pending;
 /* Optional PID1 normal-shutdown router. Disabled until a physical-stop
  * consumer is bound. Signal context writes only the first requested signal;
  * this is distinct from the current transaction's active/pending admission. */
 volatile sig_atomic_t normal_route_armed;
 volatile sig_atomic_t normal_route_requested;
 /* Final stock handoff, published only after exact physical RELEASE.
  * Zero until private cleanup; original signal and single delivery survive
  * route disarm and failed process-context raise. */
 volatile sig_atomic_t replay_signal,replay_ready,replay_delivered;
 /* Process-context OFF exclusion; signal handlers never read/write it.
  * Separate from active/pending, retained across physical shutdown_end. */
 unsigned int radio_off_owned;
 /* ON root survives parent release through WAN/IAPP; process context only. */
 unsigned int radio_on_owned;
};
extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;

static inline int wr_iot_rc_shutdown_begin(void){
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.normal_route_requested||wr_iot_rc_shutdown.replay_signal)return 0;
 wr_iot_rc_shutdown.active=1;
 /* A routed signal can win after the first check but before publication.
  * Recheck under active admission. If it won, relinquish this empty claim
  * before touching the mailbox. Clear only the duplicate pending slot after
  * switching inactive: later signals now preserve the existing route request. */
 if(wr_iot_rc_shutdown.normal_route_requested||wr_iot_rc_shutdown.replay_signal){
  wr_iot_rc_shutdown.active=0;
  wr_iot_rc_shutdown.pending=0;
  return 0;
 }
 return 1;
}
/* Called by PID 1's signal handler. Defer only normal RC shutdown requests.
 * SIGPWR and process faults retain the stock immediate path.
 * Keep the first signal; do not call RC, malloc, logging or locks here. */
static inline int wr_iot_rc_shutdown_note(int sig){
 if(sig!=SIGTERM
#ifdef SIGQUIT
     &&sig!=SIGQUIT
#endif
   )return 0;
 if(wr_iot_rc_shutdown.replay_signal){
  if(!wr_iot_rc_shutdown.replay_ready||wr_iot_rc_shutdown.replay_delivered||
     sig!=wr_iot_rc_shutdown.replay_signal)return 1;
  wr_iot_rc_shutdown.replay_delivered=1;return 0;
 }
 if(wr_iot_rc_shutdown.active){
  if(!wr_iot_rc_shutdown.pending)wr_iot_rc_shutdown.pending=sig;
  return 1;
 }
 if(wr_iot_rc_shutdown.normal_route_armed){
  if(!wr_iot_rc_shutdown.normal_route_requested)wr_iot_rc_shutdown.normal_route_requested=sig;
  return 1;
 }
 return 0;
}
/* Process-context preparation only; no default/automatic arm. The consumer
 * must retain request ownership until exact physical completion and must not
 * clear a pending request merely because a software BSS CLOSE completed. */
static inline int wr_iot_rc_shutdown_route_arm(void){
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.normal_route_requested||wr_iot_rc_shutdown.replay_signal)return 0;
 wr_iot_rc_shutdown.normal_route_armed=1;return 1;
}
/* Process-context retry only, never called from a signal handler. A failed
 * raise leaves the exact original signal ready for a later PID1 window. */
static inline int wr_iot_rc_shutdown_replay_pending(void){
 return wr_iot_rc_shutdown.replay_signal&&wr_iot_rc_shutdown.replay_ready&&
  !wr_iot_rc_shutdown.replay_delivered;
}
static inline int wr_iot_rc_shutdown_replay_step(void){
 if(!wr_iot_rc_shutdown_replay_pending())return 0;
 return raise(wr_iot_rc_shutdown.replay_signal)==0&&
  wr_iot_rc_shutdown.replay_delivered;
}
static inline int wr_iot_rc_shutdown_end(void){
 int pending;
 /* Once inactive, a new signal takes the stock path. Read the deferred
  * slot only after this switch so a late signal cannot be cleared unseen. */
 wr_iot_rc_shutdown.active=0;
 pending=wr_iot_rc_shutdown.pending;
 wr_iot_rc_shutdown.pending=0;
 return pending;
}
#endif
