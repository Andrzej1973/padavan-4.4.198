#ifndef WR_IOT_RADIO_ON_FOLLOWUP_H
#define WR_IOT_RADIO_ON_FOLLOWUP_H
#include "radio-on-restore.h"
/* After parent RELEASED: WAN once, fresh owned network proof, LED once, then
 * paired-gated IAPP with bounded child draining. No script replay on failure. */
int wr_iot_on_followup_step(struct wr_iot_on_restore *);
/* Trusted internal disabled observer under fresh service guard. */
int wr_iot_on_followup_observed(struct wr_iot_on_restore *,int (*)(struct wr_iot_on_restore *,void *),void *);
#endif
