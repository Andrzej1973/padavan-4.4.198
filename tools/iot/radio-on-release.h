#ifndef WR_IOT_RADIO_ON_RELEASE_H
#define WR_IOT_RADIO_ON_RELEASE_H
#include "radio-on-handoff.h"
/* Read-only preflight under the retained outer admission/service guard. */
int wr_iot_on_release_current(struct wr_iot_on_restore *);
/* RC owns the historical receipt. Releases parent only after fresh preflight;
 * failed mask restore retains baseline/receipt/guards for same-context retry.
 * RELEASED is not DONE: caller still owns WAN/IAPP follow-up. */
int wr_iot_rc_radio_on_release(struct wr_iot_on_restore *);
#endif
