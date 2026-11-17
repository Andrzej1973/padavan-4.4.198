/* Reduced normal-consumer boundary for backend-only fixtures. Actual normal
 * controller availability and publication are checked by the mailbox/physical
 * composition. These actors cannot prove target or shutdown completion. */
#ifndef WR_IOT_CHECK_MAILBOX_NORMAL_CONSUMER_H
#define WR_IOT_CHECK_MAILBOX_NORMAL_CONSUMER_H
#include "rc-normal-shutdown.h"
int wr_iot_rc_normal_shutdown_terminal_arm_ready(void){
 return wr_iot_rc_shutdown.active==1&&
  (!wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.pending==SIGTERM||wr_iot_rc_shutdown.pending==SIGQUIT)&&
  !wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.replay_signal&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned;
}
#ifndef WR_IOT_CHECK_NORMAL_COMMIT_EXTERNAL
void wr_iot_rc_normal_shutdown_arm_commit(void){wr_iot_rc_shutdown.normal_route_armed=1;}
#endif
#endif
