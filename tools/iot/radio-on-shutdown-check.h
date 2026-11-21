#ifndef WR_IOT_RADIO_ON_SHUTDOWN_CHECK_H
#define WR_IOT_RADIO_ON_SHUTDOWN_CHECK_H
#include "radio-on-restore.h"
#include "rc-quiesce.h"
/* Read-only exact post-handoff terminal witnesses. CLOSED is from the new
 * owned OFF, REJECTED is pre-OPEN rollback; neither authorizes profile restore. */
int wr_iot_on_shutdown_closed_current(struct wr_iot_on_restore *,const struct wr_iot_rc_quiesce *);
int wr_iot_on_shutdown_rejected_current(struct wr_iot_on_restore *);
#endif
