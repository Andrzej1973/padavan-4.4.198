/* Fresh read-only software status for retained rebind owners. Caller serializes
 * runner/stop; no copy/adoption of a live context, no hardware acceptance. */
#ifndef WR_IOT_REBIND_OBSERVE_H
#define WR_IOT_REBIND_OBSERVE_H
#include "rebind-active-stop.h"
int wr_iot_rebind_active_observed(const struct wr_iot_rebind_runner *,
 const struct wr_iot_control_result *);
int wr_iot_rebind_off_observed(const struct wr_iot_rebind_runner *,
 const struct wr_iot_rebind_active_stop *,const struct wr_iot_control_result *);
int wr_iot_rebind_off_closed(const struct wr_iot_rebind_runner *,
 const struct wr_iot_rebind_active_stop *,const struct wr_iot_control_result *,
 struct wr_iot_driver_closed_result *);
#endif
