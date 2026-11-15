#ifndef WR_IOT_RADIO_OFF_AUTH_H
#define WR_IOT_RADIO_OFF_AUTH_H
#include "radio-off-policy.h"
#include "physical-stop-wire.h"
enum wr_iot_off_auth_result {WR_OFF_AUTH_REFUSED,WR_OFF_AUTH_RETURNED,WR_OFF_AUTH_UNCERTAIN};
/* Caller marks an attempt before calling. RETURNED is SDK return only, not
 * authentication readiness. No RSSI writes while all2GHz interfaces are DOWN. */
enum wr_iot_off_auth_result wr_iot_rc_radio_off_auth(const struct wr_iot_radio_off_policy *,const struct wr_iot_physical_stop_request *);
#endif
