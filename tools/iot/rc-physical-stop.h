#ifndef WR_IOT_RC_PHYSICAL_STOP_H
#define WR_IOT_RC_PHYSICAL_STOP_H
#include "control-record.h"
#include "physical-stop-wire.h"
struct wr_iot_rc_physical_intent {unsigned restart,radio_on,reload;};
/* Private RC main-loop API, never a signal handler. Returns1 after claiming
 * the intent, including recoverable preparation failure. step/take must finish
 * that claim; restart additionally requires the verified resume consumer.
 * Does not execute the stock restart or authorize reopen. */
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *);
/* ACTIVE -> existing normal OFF before physical work. Caller provides a fresh
 * private OFF envelope; desired ON settings stay in retained process memory. */
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent *,
 const struct wr_iot_control_request *);
struct wr_iot_rc_physical_resume {
 struct wr_iot_rc_physical_intent intent;
 struct wr_iot_physical_stop_request physical;
 int resume_needed;
 struct wr_iot_request desired;
};
/* Private read-only snapshot after exact RELEASE; never copies a live owner
 * context, consumes intent, starts Main or releases guards. Contains secrets:
 * caller must wipe after use; never publish in status/log/mailbox. */
int wr_iot_rc_physical_resume_read(struct wr_iot_rc_physical_resume *);
/* Strong prepared net_wifi adapter. Fixed six AUX/Guest slots, never Main.
 * Success is administrative DOWN only, not driver completion. */
int wr_iot_rc_physical_aux_down(unsigned int);
int wr_iot_rc_physical_pending(void);
void wr_iot_rc_physical_step(void);
/* Read copied restart intent after physical RELEASE while guards remain held.
 * Does not consume intent, release admission or authorize reopen. The verified
 * restart/fresh-identity consumer remains required before this can complete. */
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent *);
/* Exactly one terminal consumption:1 STOP RELEASE acknowledged,-1 cancelled/refused,
 * 0 pending/absent/foreign. Captured intent is returned only at terminal state. */
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent *);
struct wr_iot_restart_restore;
/* Exact ACTIVE resume consumer; failed proof/mask restore retains ownership.
 * Success retires only old private baseline, never restores the live profile. */
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore *);
#endif
