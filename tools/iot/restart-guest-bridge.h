#ifndef WR_IOT_RESTART_GUEST_BRIDGE_H
#define WR_IOT_RESTART_GUEST_BRIDGE_H
#include "restart-main-bridge.h"
/* Fixed ra1->br0, attach only while DOWN. Separate current predicate observes
 * membership after UP too. No isolation/firewall readiness inferred. */
int wr_iot_restart_guest_bridge_current(void);
enum wr_iot_main_bridge_result wr_iot_restart_guest_bridge_attach(void);
#endif
