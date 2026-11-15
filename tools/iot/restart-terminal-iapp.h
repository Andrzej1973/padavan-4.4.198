#ifndef WR_IOT_RESTART_TERMINAL_IAPP_H
#define WR_IOT_RESTART_TERMINAL_IAPP_H
#include "restart-iapp-child.h"
#include "radio-stop-fence.h"
struct wr_iot_terminal_iapp {
 pid_t owner;int busy,guard,attempted,result;
 struct wr_iot_radio_stop_fence fence;
 struct wr_iot_iapp_child *child;
};
/* New process-context service transaction AFTER consumed physical completion.
 * Stable child storage must outlive terminal. No radio restart or WAN operation. */
int wr_iot_terminal_iapp_begin(struct wr_iot_terminal_iapp *,struct wr_iot_iapp_child *);
/* 1 script returned0,-1 confirmed failure/cancellation,0 pending/unknown. */
int wr_iot_terminal_iapp_step(struct wr_iot_terminal_iapp *);
#endif
