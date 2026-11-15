#ifndef WR_IOT_RADIO_ON_PREHANDOFF_H
#define WR_IOT_RADIO_ON_PREHANDOFF_H
#include "radio-on-restore.h"
/* Read-only shutdown witness before any ra2 rebind handoff; no profile restore,
 * Main DOWN, physical retirement, guard release or cleanup permission alone. */
int wr_iot_on_prehandoff_cancel_current(struct wr_iot_on_restore *);
#endif
