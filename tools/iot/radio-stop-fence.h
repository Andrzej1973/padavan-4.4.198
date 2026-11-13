/* Process-context physical-radio call fence, not RF/DMA retirement evidence.
 * Zero each token. Nested calls close in LIFO order. No signal-handler calls. */
#ifndef WR_IOT_RADIO_STOP_FENCE_H
#define WR_IOT_RADIO_STOP_FENCE_H
#include <sys/types.h>
struct wr_iot_radio_stop_fence {pid_t owner;unsigned level;};
int wr_iot_radio_stop_fence_begin(struct wr_iot_radio_stop_fence *);
int wr_iot_radio_stop_fence_end(struct wr_iot_radio_stop_fence *);
#endif
