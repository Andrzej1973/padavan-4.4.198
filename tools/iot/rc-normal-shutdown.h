#ifndef WR_IOT_RC_NORMAL_SHUTDOWN_H
#define WR_IOT_RC_NORMAL_SHUTDOWN_H
/* PID1 process context only. Enabled INITIAL finish may arm routing after exact
 * ACTIVE/consumer preflight under admission. Caller progresses existing
 * transaction owners first, then invokes one step per normal runtime window.
 * INITIAL_OFF is deliberately refused until its physical path is implemented. */
/* Private INITIAL finish prepare/commit pair; active admission must span both. */
int wr_iot_rc_normal_shutdown_arm_ready(void);
/* Cold parent release preflight only; exact caller proof remains mandatory. */
int wr_iot_rc_normal_shutdown_cold_arm_ready(void);
int wr_iot_rc_normal_shutdown_cold_handoff_ready(void);
void wr_iot_rc_normal_shutdown_arm_commit(void);
int wr_iot_rc_normal_shutdown_pending(void);
int wr_iot_rc_normal_shutdown_step(void);
/* Bracket each existing synchronous PID1 notification batch. An admitted
 * batch finishes before later routed shutdown progression; signals only
 * record the request. Refusal preserves the vendor flag. No mask changes. */
int wr_iot_rc_normal_notification_begin(void);
void wr_iot_rc_normal_notification_end(void);
#endif
