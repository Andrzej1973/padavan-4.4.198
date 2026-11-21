/* Process-context routed INITIAL admission. Never edits signal state.
 * Stable owner and existing outer fence must outlive all admitted operations. */
#ifndef WR_IOT_INITIAL_SHUTDOWN_OWNER_H
#define WR_IOT_INITIAL_SHUTDOWN_OWNER_H
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
struct wr_iot_initial_shutdown_owner {
 pid_t owner;int signal;
 const struct wr_iot_radio_stop_fence *fence;
};
static inline int wr_iot_initial_shutdown_current(const struct wr_iot_initial_shutdown_owner *s)
{
 return s&&s->owner==getpid()&&s->fence&&s->fence->owner==getpid()&&
  s->fence->level==1&&wr_iot_rc_shutdown.active&&
  wr_iot_rc_shutdown.normal_route_armed&&!wr_iot_rc_shutdown.replay_signal&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&
  (s->signal==SIGTERM
#ifdef SIGQUIT
   ||s->signal==SIGQUIT
#endif
  )&&wr_iot_rc_shutdown.pending==s->signal&&
  wr_iot_rc_shutdown.normal_route_requested==s->signal;
}
static inline int wr_iot_initial_shutdown_claim(struct wr_iot_initial_shutdown_owner *s,
 const struct wr_iot_radio_stop_fence *fence)
{
 struct wr_iot_initial_shutdown_owner candidate={0};
 if(!s||s->owner||s->signal||s->fence)return 0;
 candidate.owner=getpid();candidate.signal=wr_iot_rc_shutdown.normal_route_requested;
 candidate.fence=fence;
 if(!wr_iot_initial_shutdown_current(&candidate))return 0;
 *s=candidate;return 1;
}
#endif
