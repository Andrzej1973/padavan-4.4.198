#ifndef WR_IOT_RESTART_MULTICAST_CONTROLLER_H
#define WR_IOT_RESTART_MULTICAST_CONTROLLER_H
#include "restart-main-controller.h"
#include "restart-guest-controller.h"
#include "restart-multicast-policy.h"
enum wr_iot_multicast_phase {WR_MC_IDLE,WR_MC_SUBMIT,WR_MC_UNCERTAIN,WR_MC_READY};
struct wr_iot_multicast {
 pid_t owner;int busy;unsigned next,attempted;
 enum wr_iot_multicast_phase phase;
 struct wr_iot_restart_main *main;
 struct wr_iot_restart_guest *guest;
 struct wr_iot_multicast_policy policy;
};
int wr_iot_restart_multicast_begin(struct wr_iot_multicast *,struct wr_iot_restart_main *,struct wr_iot_restart_guest *);
int wr_iot_restart_multicast_step(struct wr_iot_multicast *);
#endif
