#ifndef WR_IOT_COLD_ON_RECOVERY_H
#define WR_IOT_COLD_ON_RECOVERY_H
#include "cold-on-generation.h"
/* Process context, cold origin only. Never restores after attempted Main UP.
 * -1 means baseline restored but still owned; 0 retains all resources. */
int wr_iot_cold_preup_recover(struct wr_iot_cold_generation *);
/* After restored-file and fresh DOWN proof, releases credentials/guard inside
 * the outer signal-fence cleanup, before pending shutdown replay. */
int wr_iot_cold_preup_finish(struct wr_iot_cold_generation *);
#endif
