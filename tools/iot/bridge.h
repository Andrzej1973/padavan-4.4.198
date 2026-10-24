/* Caller serializes IoT operations and quiesces the BSS before bridge changes. */
#ifndef WR_IOT_BRIDGE_H
#define WR_IOT_BRIDGE_H
#include <stddef.h>
#include "types.h"
int wr_iot_bridge_prepare(const char *,const char *,const char *,const char *,const struct wr_iot_range *,size_t);
int wr_iot_bridge_remove(void);
int wr_iot_bridge_is_owned(void);
int wr_iot_bridge_attach(void);
int wr_iot_bridge_detach(void);
/* Administrative DOWN with readback; vendor radio quiescence needs device proof.
 * Caller holds the service guard and owns the candidate ra2 generation. */
int wr_iot_bss_set_down(void);
/* Administrative UP only: caller holds the service guard and has verified
 * isolation/DHCP/DNS. Vendor radio and client connectivity need device proof. */
int wr_iot_bss_set_up(void);
/* Read-only administrative observation: owned UP bridge, sole attached ra2 UP.
 * Caller holds the service guard. This does not prove RF/client connectivity. */
int wr_iot_bss_is_active(void);
/* Read-only administrative DOWN/absent check; foreign masters are refused.
 * Caller owns the generation/guard. Does not prove vendor RF quiescence. */
int wr_iot_bss_is_down(void);
/* Exact current owned bridge gateway/mask observation; no interface mutation. */
int wr_iot_bridge_address_matches(const char *,const char *);
/* Caller installs isolation before UP and stops ra2 before either transition. */
int wr_iot_bridge_set_up(int enabled);
#endif
