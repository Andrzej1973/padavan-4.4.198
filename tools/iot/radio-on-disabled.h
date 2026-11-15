#ifndef WR_IOT_RADIO_ON_DISABLED_H
#define WR_IOT_RADIO_ON_DISABLED_H
#include "radio-on-restore.h"
#include "initial-off.h"
struct wr_iot_on_disabled {
 pid_t owner;int busy;
 struct wr_iot_on_restore *restore;
 struct wr_iot_initial_off idle;
};
/* Stable borrowed PREPARED parent. No OPEN or resource retirement permission. */
int wr_iot_on_disabled_begin(struct wr_iot_on_disabled *,struct wr_iot_on_restore *,const struct wr_iot_control_request *);
int wr_iot_on_disabled_current(struct wr_iot_on_disabled *);
/* Fresh disabled/parent/profile/auth/WAN preflight only; never releases. */
int wr_iot_on_disabled_release_current(struct wr_iot_on_disabled *);
/* RC-owned checked parent release; RELEASED still requires WAN/IAPP followup. */
int wr_iot_on_disabled_release(struct wr_iot_on_disabled *);
#endif
