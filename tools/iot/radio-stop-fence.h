/* Process-context physical-radio call fence, not RF/DMA retirement evidence.
 * Zero each token. Nested calls close in LIFO order. No signal-handler calls. */
#ifndef WR_IOT_RADIO_STOP_FENCE_H
#define WR_IOT_RADIO_STOP_FENCE_H
#include <sys/types.h>
struct wr_iot_radio_stop_fence {pid_t owner;unsigned level;};
int wr_iot_radio_stop_fence_begin(struct wr_iot_radio_stop_fence *);
int wr_iot_radio_stop_fence_end(struct wr_iot_radio_stop_fence *);
/* Outer fence only. Caller prevalidates all fallible work. Cleanup must be
 * infallible, bounded, non-reentrant and must not alter admission/signals/fence.
 * Runs after successful mask restore, while admission is active, before pending
 * shutdown replay. Failed restore retains token and never invokes cleanup. */
int wr_iot_radio_stop_fence_end_cleanup(struct wr_iot_radio_stop_fence *,void (*)(void *),void *);
#endif
