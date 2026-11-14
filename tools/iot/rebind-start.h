#ifndef WR_IOT_REBIND_START_H
#define WR_IOT_REBIND_START_H
#include "start-admission.h"
#include "physical-rebind-controller.h"
struct wr_iot_rebind_start {
 struct wr_iot_start_admission admission;
 struct wr_iot_physical_stop_request physical;
 struct wr_iot_driver_identity identity;
 unsigned char open_id[16];
 pid_t owner;
};
/* Caller retains exact physical completion, fresh OPEN ID and outer guards.
 * Initial-idle and old same-epoch CLOSE witnesses are never substituted. */
int wr_iot_rebind_start_begin(struct wr_iot_rebind_start *,
 const struct wr_iot_physical_stop_request *,const unsigned char *);
int wr_iot_rebind_start_stage(struct wr_iot_rebind_start *,
 const char *(*)(void *,const char *),void *,int,int,int);
#endif
