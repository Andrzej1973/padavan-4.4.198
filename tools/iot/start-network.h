/* Experimental pre-OPEN network preparation. Caller retains startup admission,
 * exact immutable request and RC shutdown/service ownership throughout. This
 * object neither commits DNS nor releases baseline. A phase0 object must
 * start only with exact staged network0/firewall0 values. A failed operation may
 * have mutated resources: no retry or reset before full rollback. */
#ifndef WR_IOT_START_NETWORK_H
#define WR_IOT_START_NETWORK_H
#include "start-admission.h"
#include "request.h"
enum wr_iot_start_network_phase {
 WR_IOT_NET_BRIDGE,WR_IOT_NET_QUARANTINE,WR_IOT_NET_ATTACH,WR_IOT_NET_UP,
 WR_IOT_NET_ENABLE,WR_IOT_NET_DNS,WR_IOT_NET_POLICY,WR_IOT_NET_READY,
 WR_IOT_NET_RECOVERY
};
struct wr_iot_start_network {enum wr_iot_start_network_phase phase;};
/* One phase, return1 only at READY. On failure retains snapshot and phase
 * becomes RECOVERY. No radio OPEN/close/restart or implicit rollback occurs. */
int wr_iot_start_network_step(struct wr_iot_start_network *,
 struct wr_iot_start_admission *,const struct wr_iot_request *,const unsigned char *);
#endif
