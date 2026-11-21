/* Legacy CLOSE-only host fixtures: INITIAL dispatch is forbidden. */
#ifndef WR_IOT_CHECK_INITIAL_UNREACHABLE_H
#define WR_IOT_CHECK_INITIAL_UNREACHABLE_H
#include "restart-initial-handoff.h"
int wr_iot_restart_initial_cancel_step(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_restart_initial_shutdown_step(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r,struct wr_iot_rc_quiesce*q){(void)s;(void)r;(void)q;assert(0);return 0;}
int wr_iot_restart_initial_handoff_begin(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_initial_handoff_step(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_initial_restart_receipt(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r,struct wr_iot_initial_restart_receipt*out){(void)s;(void)r;(void)out;assert(0);return 0;}
int wr_iot_rc_initial_restart_postrelease_current(const struct wr_iot_initial_restart_receipt*r){(void)r;assert(0);return 0;}
int wr_iot_rc_initial_restart_unclaimed_current(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rc_initial_restart_preopen_rejected(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rc_initial_restart_committed_closed(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rc_initial_restart_rollback_closed(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rc_initial_restart_shutdown_closed(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r,const struct wr_iot_rc_quiesce*q,struct wr_iot_driver_closed_result*out){(void)s;(void)r;(void)q;(void)out;assert(0);return 0;}
#endif
