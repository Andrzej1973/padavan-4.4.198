#ifndef WR_IOT_RC_COLD_DISABLED_COMPLETION_H
#define WR_IOT_RC_COLD_DISABLED_COMPLETION_H
#include "cold-on-disabled-release.h"
#include "restart-terminal-iapp.h"
/* Stable RC-private contexts, no public/scheduler or shutdown binding yet. */
struct wr_iot_cold_disabled_parent_release {
 struct wr_iot_cold_disabled_release *release;int busy,released;
};
enum wr_iot_cold_disabled_terminal_phase {WR_COLD_DISABLED_TERM_IDLE,WR_COLD_DISABLED_TERM_WAN,WR_COLD_DISABLED_TERM_IAPP_PENDING,
 WR_COLD_DISABLED_TERM_IAPP,WR_COLD_DISABLED_TERM_DONE,WR_COLD_DISABLED_TERM_RETAINED};
struct wr_iot_cold_disabled_terminal {
 pid_t owner;int busy,led_attempted,led_returned;
 enum wr_iot_cold_disabled_terminal_phase phase;
 struct wr_iot_cold_disabled_parent_release *parent_release;
 struct wr_iot_terminal_iapp terminal;struct wr_iot_iapp_child child;
};


int wr_iot_rc_cold_disabled_parent_release(struct wr_iot_cold_disabled_parent_release *,struct wr_iot_cold_disabled_release *);
int wr_iot_rc_cold_disabled_terminal_begin(struct wr_iot_cold_disabled_terminal *,struct wr_iot_cold_disabled_parent_release *);
int wr_iot_rc_cold_disabled_terminal_step(struct wr_iot_cold_disabled_terminal *);
int wr_iot_rc_cold_disabled_terminal_retire(struct wr_iot_cold_disabled_terminal *);
#endif
