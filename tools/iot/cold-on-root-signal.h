#ifndef WR_IOT_COLD_ON_ROOT_SIGNAL_H
#define WR_IOT_COLD_ON_ROOT_SIGNAL_H
#include "cold-on-root.h"
/* Process-context routing before a root continuation. Observes queued normal
 * signals even while the outer fence blocks delivery. 1 permits the normal
 * continuation (including an owned terminal child drain); 0 retains pending
 * shutdown; -1 checked cleanup released/wiped the root. */
int wr_iot_cold_root_signal_step(struct wr_iot_cold_root *);
#endif
