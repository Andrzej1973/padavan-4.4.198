#ifndef WR_IOT_RESTART_SERVICES_H
#define WR_IOT_RESTART_SERVICES_H
#include "restart-main-controller.h"
#include "restart-service-policy.h"
enum wr_iot_restart_services_phase {WR_SERVICES_IDLE,WR_SERVICES_SUBMIT,WR_SERVICES_UNCERTAIN,WR_SERVICES_SUBMITTED};
struct wr_iot_restart_services {
 pid_t owner;int busy;unsigned int next,attempted;
 enum wr_iot_restart_services_phase phase;
 struct wr_iot_restart_main *main;
 struct wr_iot_restart_service_policy policy;
};
/* Stable context; main/generation must outlive it. Submitted only means the
 * SDK commands returned zero, not daemon readiness or applied driver policy. */
int wr_iot_restart_services_begin(struct wr_iot_restart_services *,struct wr_iot_restart_main *);
int wr_iot_restart_services_step(struct wr_iot_restart_services *);
#endif
