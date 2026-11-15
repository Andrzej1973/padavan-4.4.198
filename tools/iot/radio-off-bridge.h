#ifndef WR_IOT_RADIO_OFF_BRIDGE_H
#define WR_IOT_RADIO_OFF_BRIDGE_H
#include "physical-stop-wire.h"
enum wr_iot_off_bridge_result {WR_OFF_BRIDGE_REFUSED,WR_OFF_BRIDGE_DETACHED,WR_OFF_BRIDGE_UNCERTAIN};
/* Fixed SDK OFF order: Guest, Main, WDS3..0, APCLI. DETACHED includes checked
 * absent optional netdev. REFUSED made no bridge mutation; UNCERTAIN must not
 * be replayed automatically. No radio/interface-UP or arbitrary names. */
enum wr_iot_off_bridge_result wr_iot_radio_off_bridge_detach(const struct wr_iot_physical_stop_request *,unsigned);
#endif
