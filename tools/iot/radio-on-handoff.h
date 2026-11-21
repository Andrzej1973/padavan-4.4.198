#ifndef WR_IOT_RADIO_ON_HANDOFF_H
#define WR_IOT_RADIO_ON_HANDOFF_H
#include "radio-on-restore.h"
#include "control-record.h"
/* One backend begin after exact envelope and fresh PREPARED proof. A refused
 * begin may retain partial admission: HANDOFF never permits begin replay. */
int wr_iot_on_restore_handoff(struct wr_iot_on_restore *,const struct wr_iot_control_request *);
/* Advance only retained backend identity; success needs exact ACTIVE proof,
 * never APPLIED status alone. No guard/baseline/receipt retirement here. */
int wr_iot_on_rebind_step(struct wr_iot_on_restore *);
/* Read-only variant for final preflight, never advances backend mutations. */
int wr_iot_on_rebind_current(struct wr_iot_on_restore *);
#endif
