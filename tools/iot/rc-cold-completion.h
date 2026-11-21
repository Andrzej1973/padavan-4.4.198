#ifndef WR_IOT_RC_COLD_COMPLETION_H
#define WR_IOT_RC_COLD_COMPLETION_H
#include "cold-on-release.h"
#include "restart-terminal-iapp.h"
/* RC-private stable caller-owned contexts, never copy while live. Public cold
 * entry and shutdown orchestration are not installed by these wrappers. */
struct wr_iot_cold_parent_release {
 struct wr_iot_cold_release *release;
 int busy,released;
};
enum wr_iot_cold_terminal_phase {WR_COLD_TERM_IDLE,WR_COLD_TERM_WAN,WR_COLD_TERM_IAPP_PENDING,
 WR_COLD_TERM_IAPP,WR_COLD_TERM_DONE,WR_COLD_TERM_RETAINED};
struct wr_iot_cold_terminal {
 pid_t owner;int busy,led_attempted,led_returned;
 enum wr_iot_cold_terminal_phase phase;
 struct wr_iot_cold_parent_release *parent_release;
 struct wr_iot_terminal_iapp terminal;struct wr_iot_iapp_child child;
};

int wr_iot_rc_cold_parent_release(struct wr_iot_cold_parent_release *,struct wr_iot_cold_release *);
int wr_iot_rc_cold_terminal_begin(struct wr_iot_cold_terminal *,struct wr_iot_cold_parent_release *);
int wr_iot_rc_cold_terminal_step(struct wr_iot_cold_terminal *);
int wr_iot_rc_cold_terminal_retire(struct wr_iot_cold_terminal *);
#endif
