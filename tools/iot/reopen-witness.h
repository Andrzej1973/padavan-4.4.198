/* Nonsecret copied post-CLOSE identity. No pointer to previous runner. */
#ifndef WR_IOT_REOPEN_WITNESS_H
#define WR_IOT_REOPEN_WITNESS_H
#include <sys/types.h>
#include "driver-api-client.h"
struct wr_iot_reopen_witness {
 pid_t owner;
 struct wr_iot_driver_attempt attempt;
 unsigned long long open_token,close_serial;
 int valid,submitted;
};
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness *);
#endif
