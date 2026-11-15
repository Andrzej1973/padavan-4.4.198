#ifndef WR_IOT_RC_NORMAL_SHUTDOWN_H
#define WR_IOT_RC_NORMAL_SHUTDOWN_H
/* PID1 process context only. Does not arm routing. Caller progresses existing
 * transaction owners first, then invokes one step per normal runtime window.
 * INITIAL_OFF is deliberately refused until its physical path is implemented. */
int wr_iot_rc_normal_shutdown_pending(void);
int wr_iot_rc_normal_shutdown_step(void);
#endif
