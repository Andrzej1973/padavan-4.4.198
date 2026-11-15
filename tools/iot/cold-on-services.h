#ifndef WR_IOT_COLD_ON_SERVICES_H
#define WR_IOT_COLD_ON_SERVICES_H
#include "cold-on-guest.h"
#include "restart-service-policy.h"
enum wr_iot_cold_services_phase {WR_COLD_SERVICES_IDLE,WR_COLD_SERVICES_SUBMIT,WR_COLD_SERVICES_UNCERTAIN,WR_COLD_SERVICES_SUBMITTED};
struct wr_iot_cold_services {
 pid_t owner;int busy;unsigned int next,attempted;
 enum wr_iot_cold_services_phase phase;
 struct wr_iot_cold_guest *guest;
 struct wr_iot_restart_service_policy policy;
};
/* Stable context; guest/Main/generation must outlive it. Submitted only means the
 * SDK commands returned zero, not daemon readiness or applied driver policy. */
int wr_iot_cold_services_begin(struct wr_iot_cold_services *,struct wr_iot_cold_guest *);
int wr_iot_cold_services_step(struct wr_iot_cold_services *);
#endif
