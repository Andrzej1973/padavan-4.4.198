#ifndef WR_IOT_RADIO_ON_MULTICAST_H
#define WR_IOT_RADIO_ON_MULTICAST_H
#include "radio-on-main.h"
#include "radio-on-guest.h"
#include "restart-multicast-policy.h"
enum wr_iot_on_multicast_phase {WR_ON_MC_IDLE,WR_ON_MC_SUBMIT,WR_ON_MC_UNCERTAIN,WR_ON_MC_READY};
struct wr_iot_on_multicast {
 pid_t owner;int busy;unsigned next,attempted;
 enum wr_iot_on_multicast_phase phase;
 struct wr_iot_on_main *main;
 struct wr_iot_on_guest *guest;
 struct wr_iot_multicast_policy policy;
};
int wr_iot_on_multicast_begin(struct wr_iot_on_multicast *,struct wr_iot_on_main *,struct wr_iot_on_guest *);
int wr_iot_on_multicast_step(struct wr_iot_on_multicast *);
/* Read-only after rebind ACTIVE proof: never runs pre-OPEN Main checks. */
int wr_iot_on_multicast_observed(struct wr_iot_on_multicast *);
#endif
