/* Retained physical-restart resume composition. Caller holds the outer physical
 * restart guards and serializes this object; no scheduler hook is installed. */
#ifndef WR_IOT_REBIND_RUNNER_H
#define WR_IOT_REBIND_RUNNER_H
#include "start-runner.h"
#include "rebind-network.h"
#include "rebind-rollback.h"
#include "rebind-commit.h"
#include "rebind-closed-rollback.h"
struct wr_iot_rebind_runner {
 pid_t owner;
 int busy;
 enum wr_iot_start_runner_phase phase;
 struct wr_iot_control_request input;
 struct wr_iot_rebind_start start;
 struct wr_iot_start_network network;
 struct wr_iot_rebind_open_controller open;
 struct wr_iot_start_close close;
 struct wr_iot_start_network_rollback rollback;
 struct wr_iot_start_commit commit;
 struct wr_iot_precreated_stop stop;
};
/* Fresh transaction ID; validated copied ON settings, exact retained physical
 * RELEASE and current mode. Reinitializing a retained context is refused. */
int wr_iot_rebind_runner_begin(struct wr_iot_rebind_runner *,
 const struct wr_iot_control_request *,const struct wr_iot_physical_stop_request *,int,int,int);
enum wr_iot_result_state wr_iot_rebind_runner_step(struct wr_iot_rebind_runner *);
enum wr_iot_result_state wr_iot_rebind_runner_continue(struct wr_iot_rebind_runner *,
 const char *,unsigned long long);
#endif
