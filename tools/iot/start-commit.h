/* Final startup commit. DNS commit is attempted once; uncertainty is retained.
 * After DNS commit, recovery must use normal OFF, never startup DNS abort.
 * ACTIVE here is software commit only, not physical runtime acceptance. */
#ifndef WR_IOT_START_COMMIT_H
#define WR_IOT_START_COMMIT_H
#include "start-network.h"
#include "driver-open-controller.h"
enum wr_iot_start_commit_phase {
 WR_IOT_COMMIT_IDLE,WR_IOT_COMMIT_DNS_UNCERTAIN,
 WR_IOT_COMMIT_DNS_COMMITTED,WR_IOT_COMMIT_ACTIVE
};
struct wr_iot_start_commit {
 pid_t owner;
 struct wr_iot_driver_attempt attempt;
 unsigned long long open_token;
 enum wr_iot_start_commit_phase phase;
};
int wr_iot_start_commit_step(struct wr_iot_start_commit *,
 struct wr_iot_start_admission *,const struct wr_iot_start_network *,
 const struct wr_iot_open_controller *,const struct wr_iot_request *);
#endif
