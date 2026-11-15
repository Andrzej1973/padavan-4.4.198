#ifndef WR_IOT_COLD_ON_POLICY_H
#define WR_IOT_COLD_ON_POLICY_H
#include <sys/types.h>
#include "restart-service-policy.h"
#include "restart-multicast-policy.h"
/* Nonsecret policy snapshot; no borrowed parent pointers or client keys. */
struct wr_iot_cold_policy {
 pid_t owner;int guest,isolate;
 struct wr_iot_restart_service_policy services;
 struct wr_iot_multicast_policy multicast;
};
/* Caller continuously holds the service guard. Software/policy and process
 * liveness observation only, not firmware retirement or daemon ownership. */
int wr_iot_cold_policy_current(const struct wr_iot_cold_policy *);
#endif
