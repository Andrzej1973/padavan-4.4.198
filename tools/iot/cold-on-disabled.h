#ifndef WR_IOT_COLD_ON_DISABLED_H
#define WR_IOT_COLD_ON_DISABLED_H
#include "cold-on-owner.h"
#include "initial-off.h"
/* Never-opened ra2 software OFF proof, no physical RELEASE fabrication. */
struct wr_iot_cold_disabled {
 pid_t owner;int busy;struct wr_iot_cold_owner *parent;
 struct wr_iot_initial_off idle;
};
int wr_iot_cold_disabled_begin(struct wr_iot_cold_disabled *,struct wr_iot_cold_owner *);
int wr_iot_cold_disabled_current(struct wr_iot_cold_disabled *);
#endif
