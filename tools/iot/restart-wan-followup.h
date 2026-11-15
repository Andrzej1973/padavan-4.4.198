#ifndef WR_IOT_RESTART_WAN_FOLLOWUP_H
#define WR_IOT_RESTART_WAN_FOLLOWUP_H
#include <sys/types.h>
#include "restart-wan-plan.h"
struct wr_iot_wan_followup_state {pid_t owner;int radio_on,attempted,returned;enum wr_iot_wan_followup plan;};
int wr_iot_wan_followup_capture(struct wr_iot_wan_followup_state *,int);
/* Caller must prove physical terminal take completed before invoking. Holds
 * while shutdown admission is active/pending.1 means SDK call returned, not WAN
 * ready. An attempted call is never repeated, including after reentrancy. */
int wr_iot_wan_followup_step(struct wr_iot_wan_followup_state *);
int wr_iot_rc_restart_wan_current(int,enum wr_iot_wan_followup);
int wr_iot_rc_restart_led_on(void);
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup);
#endif
