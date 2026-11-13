/* Pre-OPEN rollback only. Caller serializes all contexts, retains immutable
 * attempt history and shutdown/service ownership. Never use after a possibly
 * submitted OPEN or DNS commit. Such paths require their own recovery owner. */
#ifndef WR_IOT_START_NETWORK_ROLLBACK_H
#define WR_IOT_START_NETWORK_ROLLBACK_H
#include "start-network.h"
#include "driver-open-controller.h"
enum wr_iot_start_rollback_phase {
 WR_IOT_ROLL_BRIDGE_DOWN,WR_IOT_ROLL_DETACH,WR_IOT_ROLL_REMOVE,
 WR_IOT_ROLL_DNS,WR_IOT_ROLL_SETTINGS,WR_IOT_ROLL_OBSERVE,
 WR_IOT_ROLL_FINISH,WR_IOT_ROLL_DONE
};
struct wr_iot_start_network_rollback {
 enum wr_iot_start_rollback_phase phase;
 pid_t owner;
};
/* One bounded phase. Failure preserves current phase, startup snapshot/guard.
 * Caller must keep network owner in RECOVERY and prohibit further OPEN. */
int wr_iot_start_network_rollback_step(struct wr_iot_start_network_rollback *,
 struct wr_iot_start_network *,struct wr_iot_start_admission *,
 const struct wr_iot_open_controller *,const unsigned char *);
#endif
