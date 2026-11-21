#ifndef WR_IOT_CONTROL_CHANNEL_H
#define WR_IOT_CONTROL_CHANNEL_H
#include "control-mailbox.h"
#include <time.h>
#ifndef WR_IOT_CONTROL_DIRECTORY
#define WR_IOT_CONTROL_DIRECTORY "/var/run/wr-iot-control"
#endif
static inline unsigned long long wr_iot_control_now(void){
 struct timespec ts;
 if(clock_gettime(CLOCK_MONOTONIC,&ts)||ts.tv_sec<=0)return 0;
 return (unsigned long long)ts.tv_sec;
}
int wr_iot_rc_submit(const struct wr_iot_request *,char [33]);
int wr_iot_rc_submit_config(const struct wr_iot_saved_config *,char [33]);
int wr_iot_rc_submit_save(const struct wr_iot_saved_config *,int explicit_save,char [33]);
int wr_iot_rc_status(const char *,struct wr_iot_control_result *);
/* Read-only status backend: return exactly 1 only when this transaction's
 * retained expected state still matches live resources. Must serialize with
 * all radio/network writers, cover enabled AND disabled requests, and reject
 * missing snapshots, changed generations or incomplete recovery. Module or
 * interface presence alone is insufficient. No weak success fallback. */
int wr_iot_activation_result_observed(const struct wr_iot_control_result *);
struct wr_iot_save_backend_hooks {
 enum wr_iot_result_state (*execute)(const struct wr_iot_control_request *);
 enum wr_iot_result_state (*progress)(const char *,unsigned long long);
 int (*terminal)(const struct wr_iot_control_result *);
};
/* Single-process, once-only registration before any active queue operation.
 * Unregistered/fork-inherited callbacks never execute Save requests. */
int wr_iot_rc_register_save_backend(const struct wr_iot_save_backend_hooks *);
int wr_iot_rc_register_edit_backend(const struct wr_iot_save_backend_hooks *);
int wr_iot_rc_submit_edit(const struct wr_iot_saved_config *,const char *,
 enum wr_iot_config_edit_mode,enum wr_iot_config_key_action,char[33]);
int wr_iot_rc_dispatch(void);
/* Explicit same-process continuation; never reclaim/replay request credentials.
 * Strong backend must match retained ID+creation time to its live owner. */
int wr_iot_rc_continue(void);
/* Read-only same-process scheduler predicate; never reconstruct from mailbox. */
int wr_iot_rc_pending(void);
enum wr_iot_result_state wr_iot_activation_continue(const char *,unsigned long long);

/* RC backend must hold the service guard, validate current mode/routes, own
 * rollback and return APPLIED only after observed success, REJECTED only before
 * mutation or after complete recovery, otherwise RECOVERY. Strong unresolved
 * symbol intentionally prevents shipping a transport-only working feature.
 * The complete claimed envelope supplies the transaction ID and creation
 * time for retained expected-state/recovery records. Never persist the
 * credentials merely to implement a status query; copy only what is needed
 * into private controller-owned state before returning. */
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *);
/* Mailbox APPLIED publication gate: arm only exact fresh ACTIVE; OFF skips.
 * Failure retains the existing continuation/admission; never execute again. */
int wr_iot_rc_backend_applied_route(const char *,unsigned long long);
/* Configuration-only backend: never activation/APPLIED or flash durability. */
enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *);
enum wr_iot_result_state wr_iot_rc_config_continue(const char *,unsigned long long);
int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *);
int wr_iot_rc_config_observed(const struct wr_iot_control_result *);
int wr_iot_configuration_result_observed(const struct wr_iot_control_result *);
#endif
