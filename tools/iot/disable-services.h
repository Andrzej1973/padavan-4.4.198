/* Candidate normal-OFF adapter. Outer controller owns RF quiescence,
 * quarantine, current radio/profile preservation and bridge teardown. */
#ifndef WR_IOT_DISABLE_SERVICES_H
#define WR_IOT_DISABLE_SERVICES_H
#include "request-snapshot.h"
struct wr_iot_disable_services {
 struct wr_iot_request_snapshot settings;
 int committed;
};
/* Read-only capture under the existing outer service guard. */
int wr_iot_disable_services_begin(struct wr_iot_disable_services *);
int wr_iot_disable_services_cancel(struct wr_iot_disable_services *);
/* ISOLATE after the outer driver QUIESCE: close current snapshot gates then
 * reapply/observe IPv4+IPv6 quarantine with bridge retained for services.
 * Failure retains snapshot/guard and any partially closed gates for retry. */
int wr_iot_disable_services_isolate(struct wr_iot_disable_services *);
/* After QUIESCE/ISOLATE, before removing the owned bridge. Failed DNS prepare
 * or commit retains all state for retry; no automatic bridge/radio reopening. */
int wr_iot_disable_services_apply(struct wr_iot_disable_services *);
/* After DNS commit and bridge/profile teardown. Does not prove radio/profile
 * teardown itself. Caller must complete final OBSERVE before releasing guard. */
int wr_iot_disable_services_finish(struct wr_iot_disable_services *);
#endif
