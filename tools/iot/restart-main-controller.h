#ifndef WR_IOT_RESTART_MAIN_CONTROLLER_H
#define WR_IOT_RESTART_MAIN_CONTROLLER_H
#include "restart-generation.h"
#include "restart-main-up.h"
#include "physical-rebind-controller.h"
enum wr_iot_restart_main_phase {WR_MAIN_IDLE,WR_MAIN_WAIT,WR_MAIN_NOT_SUBMITTED,WR_MAIN_READY};
struct wr_iot_restart_main {
 pid_t owner;int busy;
 int bridge_attempted;
 enum wr_iot_restart_main_phase phase;
 struct wr_iot_restart_generation *generation;
 unsigned char open_id[16];
 struct wr_iot_driver_identity identity;
};
/* Same stable objects retained throughout. Main UP at most once; no completion
 * or baseline release implied. Fresh rebind probe may be repeated read-only. */
int wr_iot_restart_main_begin(struct wr_iot_restart_main *,struct wr_iot_restart_generation *,const unsigned char *);
int wr_iot_restart_main_step(struct wr_iot_restart_main *);
/* One bridge mutation attempt after fresh Main READY. Subsequent calls only
 * observe membership; failure retains generation/baseline and outer guards. */
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main *);
#endif
