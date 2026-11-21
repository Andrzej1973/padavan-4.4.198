#ifndef WR_IOT_COLD_ON_ROOT_RECOVERY_H
#define WR_IOT_COLD_ON_ROOT_RECOVERY_H
#include "cold-on-root.h"
/* Explicit irreversible cancellation before attempted Main UP. Restore only
 * the owned baseline, then release/wipe before pending normal signal replay.
 * 1 root released, 0 retained. No generator, Main UP or native fallback. */
int wr_iot_cold_root_preup_recover(struct wr_iot_cold_root *);
#endif
