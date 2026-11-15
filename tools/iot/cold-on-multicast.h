#ifndef WR_IOT_COLD_ON_MULTICAST_H
#define WR_IOT_COLD_ON_MULTICAST_H
#include "cold-on-main.h"
#include "cold-on-guest.h"
#include "restart-multicast-policy.h"
enum wr_iot_cold_multicast_phase {WR_COLD_MC_IDLE,WR_COLD_MC_SUBMIT,WR_COLD_MC_UNCERTAIN,WR_COLD_MC_READY};
struct wr_iot_cold_multicast {
 pid_t owner;int busy;unsigned next,attempted;
 enum wr_iot_cold_multicast_phase phase;
 struct wr_iot_cold_main *main;
 struct wr_iot_cold_guest *guest;
 struct wr_iot_multicast_policy policy;
};
int wr_iot_cold_multicast_begin(struct wr_iot_cold_multicast *,struct wr_iot_cold_main *,struct wr_iot_cold_guest *);
int wr_iot_cold_multicast_step(struct wr_iot_cold_multicast *);
/* Read-only after separately proven startup ACTIVE: never runs pre-OPEN Main checks. */
int wr_iot_cold_multicast_observed(struct wr_iot_cold_multicast *);
#endif
