#ifndef WR_IOT_RC_PHYSICAL_STOP_H
#define WR_IOT_RC_PHYSICAL_STOP_H
struct wr_iot_rc_physical_intent {unsigned restart,radio_on,reload;};
/* Private RC main-loop API, never a signal handler. Returns1 after claiming
 * the intent, including recoverable preparation failure. step/take must finish
 * that claim; restart additionally requires the verified resume consumer.
 * Does not execute the stock restart or authorize reopen. */
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *);
/* Strong prepared net_wifi adapter. Fixed six AUX/Guest slots, never Main.
 * Success is administrative DOWN only, not driver completion. */
int wr_iot_rc_physical_aux_down(unsigned int);
int wr_iot_rc_physical_pending(void);
void wr_iot_rc_physical_step(void);
/* Read copied restart intent after physical RELEASE while guards remain held.
 * Does not consume intent, release admission or authorize reopen. The verified
 * restart/fresh-identity consumer remains required before this can complete. */
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent *);
/* Exactly one terminal consumption:1 STOP RELEASE acknowledged,-1 cancelled/refused,
 * 0 pending/absent/foreign. Captured intent is returned only at terminal state. */
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent *);
#endif
