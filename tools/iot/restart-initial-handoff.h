#ifndef WR_IOT_RESTART_INITIAL_HANDOFF_H
#define WR_IOT_RESTART_INITIAL_HANDOFF_H
#include "restart-restore.h"
int wr_iot_restart_initial_handoff_begin(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_restart_initial_handoff_step(struct wr_iot_restart_restore *);
/* Backend must validate this exact prepared parent and typed INITIAL origin;
 * implementations are separate from legacy rebind and cold-owner APIs. */
int wr_iot_rc_initial_restart_start_begin(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_start_progress(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
/* Pending TERM/QUIT: advance only pre-OPEN cancellation/recovery, never START. */
int wr_iot_rc_initial_restart_cancel_progress(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_preopen_rejected(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_unclaimed_current(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_rollback_closed(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_committed_closed(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_rc_initial_restart_active_current(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
int wr_iot_restart_initial_active_current(struct wr_iot_restart_restore *);
/* Returns 1 only for verified never-OPEN rollback, retains parent ownership. */
int wr_iot_restart_initial_cancel_step(struct wr_iot_restart_restore *);
/* Infallible RC-private callback primitive after full finish preflight. */
void wr_iot_rc_initial_restart_detach_commit(void);
struct wr_iot_rc_quiesce;
/* 0 retained, 1 verified never-OPEN rollback, 2 verified normal CLOSED. */
int wr_iot_restart_initial_shutdown_step(struct wr_iot_restart_restore *,const struct wr_iot_control_request *,struct wr_iot_rc_quiesce *);
int wr_iot_rc_initial_restart_shutdown_begin(struct wr_iot_restart_restore *,const struct wr_iot_control_request *,const struct wr_iot_control_request *,struct wr_iot_rc_quiesce *);
int wr_iot_rc_initial_restart_shutdown_progress(struct wr_iot_restart_restore *,const struct wr_iot_control_request *,struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
int wr_iot_rc_initial_restart_shutdown_closed(struct wr_iot_restart_restore *,const struct wr_iot_control_request *,const struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
/* Nonsecret identity retained across parent/profile credential cleanup. */
struct wr_iot_initial_restart_receipt {
 char id[33];unsigned long long created,open_token;
 struct wr_iot_driver_identity identity;
};
int wr_iot_rc_initial_restart_receipt(struct wr_iot_restart_restore *,const struct wr_iot_control_request *,struct wr_iot_initial_restart_receipt *);
int wr_iot_rc_initial_restart_postrelease_current(const struct wr_iot_initial_restart_receipt *);
int wr_iot_rc_initial_restart_postrelease_shutdown_begin(const struct wr_iot_initial_restart_receipt *,const struct wr_iot_control_request *,struct wr_iot_rc_quiesce *);
int wr_iot_rc_initial_restart_postrelease_shutdown_closed(const struct wr_iot_initial_restart_receipt *,const struct wr_iot_rc_quiesce *);
#endif
