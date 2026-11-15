#ifndef WR_IOT_COLD_ON_POSTSHUTDOWN_H
#define WR_IOT_COLD_ON_POSTSHUTDOWN_H
#include "rc-cold-shutdown.h"
enum wr_iot_cold_stop_phase {WR_COLD_STOP_IDLE,WR_COLD_STOP_ADMITTED,WR_COLD_STOP_DRAIN,
 WR_COLD_STOP_CLOSED,WR_COLD_STOP_REJECTED,WR_COLD_STOP_RETAINED};
/* Stable caller-owned state. No new OPEN, Main reset or profile rollback. */
struct wr_iot_cold_stop {
 pid_t owner;int busy,off_attempted;enum wr_iot_cold_stop_phase phase;
 struct wr_iot_cold_owner *parent;struct wr_iot_cold_handoff *handoff;
 struct wr_iot_control_request input;struct wr_iot_rc_quiesce off;
};
int wr_iot_cold_postshutdown_begin(struct wr_iot_cold_stop *,struct wr_iot_cold_owner *,
 struct wr_iot_cold_handoff *,const struct wr_iot_control_request *);
/* 1 exact CLOSED or separate completed pre-OPEN rejection, never cleanup. */
int wr_iot_cold_postshutdown_step(struct wr_iot_cold_stop *);
#endif
