/* Initial never-opened OFF observation, not CLOSE or RF retirement proof.
 * Zero initialize once; retains only nonsecret transaction/driver identity. */
#ifndef WR_IOT_INITIAL_OFF_H
#define WR_IOT_INITIAL_OFF_H
#include <sys/types.h>
#include "control-record.h"
#include "precreated-idle-wire.h"
struct wr_iot_initial_off {
 pid_t owner;
 char id[33];unsigned long long created;
 unsigned char nonce[16];
 struct wr_iot_idle_result idle;
 int ready;
};
int wr_iot_initial_off_begin(struct wr_iot_initial_off *,const struct wr_iot_control_request *);
/* Caller holds service guard; read-only current observation for same owner. */
int wr_iot_initial_off_observed(const struct wr_iot_initial_off *);
#endif
