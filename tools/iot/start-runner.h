/* Serialized startup composition; persistent caller-owned state. Not yet bound
 * to production RC. All recovery contexts must survive failed step calls. */
#ifndef WR_IOT_START_RUNNER_H
#define WR_IOT_START_RUNNER_H
#include "control-record.h"
#include "start-commit.h"
#include "start-closed-rollback.h"
#include "precreated-stop.h"
enum wr_iot_start_runner_phase {
 WR_IOT_RUN_IDLE,WR_IOT_RUN_STAGE,WR_IOT_RUN_NETWORK,WR_IOT_RUN_OPEN,
 WR_IOT_RUN_COMMIT,WR_IOT_RUN_COMMITTED_OFF,WR_IOT_RUN_CLOSE,WR_IOT_RUN_PRE_ROLLBACK,
 WR_IOT_RUN_CLOSED_ROLLBACK,WR_IOT_RUN_UNCERTAIN,
 WR_IOT_RUN_ACTIVE,WR_IOT_RUN_REJECTED
};
struct wr_iot_start_runner {
 pid_t owner;
 enum wr_iot_start_runner_phase phase;
 struct wr_iot_control_request input;
 unsigned char nonce[16];
 struct wr_iot_start_admission admission;
 struct wr_iot_start_network network;
 struct wr_iot_open_controller open;
 struct wr_iot_start_close close;
 struct wr_iot_start_network_rollback rollback;
 struct wr_iot_start_commit commit;
 struct wr_iot_precreated_stop stop;
};
/* Initialize once with a claimed, validated ON request and current mode.
 * Copies only after bounded string validation; never reinitialize a live owner. */
int wr_iot_start_runner_begin(struct wr_iot_start_runner *,
 const struct wr_iot_control_request *,int,int,int);
/* One phase; RECOVERY result retains shutdown and service ownership. Caller
 * continues this same object rather than replaying a claimed request. */
enum wr_iot_result_state wr_iot_start_runner_step(struct wr_iot_start_runner *);
#endif
