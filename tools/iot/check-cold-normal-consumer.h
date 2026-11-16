/* Reduced normal-consumer actor for legacy cold-only fixtures. These fixtures
 * do not link the controller or prove its availability/lifecycle. The actual
 * controller is exercised by check-cold-normal-backend-composition.py and
 * check-normal-shutdown-arm.py. Publish the real route bit so signal tests
 * cannot silently keep the historical stock-replay behavior. */
#include "rc-normal-shutdown.h"
int wr_iot_rc_normal_shutdown_cold_arm_ready(void)
{
 return wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  wr_iot_rc_shutdown.radio_off_owned==1&&!wr_iot_rc_shutdown.radio_on_owned&&
  !wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.replay_signal;
}
void wr_iot_rc_normal_shutdown_arm_commit(void)
{wr_iot_rc_shutdown.normal_route_armed=1;}
