#ifndef WR_IOT_RESTART_TERMINAL_IAPP_H
#define WR_IOT_RESTART_TERMINAL_IAPP_H
#include "restart-iapp-child.h"
#include "radio-stop-fence.h"
struct wr_iot_terminal_iapp {
 pid_t owner;int busy,guard,attempted,result,shutdown_held;
 struct wr_iot_radio_stop_fence fence;
 struct wr_iot_iapp_child *child;
};
/* New process-context service transaction AFTER consumed physical completion.
 * Stable child storage must outlive terminal. No radio restart or WAN operation. */
int wr_iot_terminal_iapp_begin(struct wr_iot_terminal_iapp *,struct wr_iot_iapp_child *);
/* 1 script returned0,-1 confirmed failure/cancellation,0 pending/unknown. */
int wr_iot_terminal_iapp_step(struct wr_iot_terminal_iapp *);
/* Pending normal shutdown only. Drain an existing child (never launch), then
 * retain the outer fence/guard until the parent proves its shutdown terminal.
 * 1 drained/cancelled, 0 pending/unknown/refused; result is not service success. */
int wr_iot_terminal_iapp_shutdown_drain(struct wr_iot_terminal_iapp *);
/* Caller must first prove parent resource completion. Cleanup runs after the
 * service guard is released and before pending signal replay. Failed unmask
 * retains this exact terminal; callback must be infallible and not free its
 * containing storage (the live fence remains addressable until return). */
int wr_iot_terminal_iapp_shutdown_finish(struct wr_iot_terminal_iapp *,void (*)(void *),void *);
#endif
