#ifndef WR_IOT_RADIO_ON_SERVICES_H
#define WR_IOT_RADIO_ON_SERVICES_H
#include "radio-on-guest.h"
#include "restart-service-policy.h"
enum wr_iot_on_services_phase {WR_ON_SERVICES_IDLE,WR_ON_SERVICES_SUBMIT,WR_ON_SERVICES_UNCERTAIN,WR_ON_SERVICES_SUBMITTED};
struct wr_iot_on_services {
 pid_t owner;int busy;unsigned int next,attempted;
 enum wr_iot_on_services_phase phase;
 struct wr_iot_on_guest *guest;
 struct wr_iot_restart_service_policy policy;
};
/* Stable context; guest/Main/generation must outlive it. Submitted only means the
 * SDK commands returned zero, not daemon readiness or applied driver policy. */
int wr_iot_on_services_begin(struct wr_iot_on_services *,struct wr_iot_on_guest *);
int wr_iot_on_services_step(struct wr_iot_on_services *);
#endif
