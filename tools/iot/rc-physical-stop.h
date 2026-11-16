#ifndef WR_IOT_RC_PHYSICAL_STOP_H
#define WR_IOT_RC_PHYSICAL_STOP_H
#include "control-record.h"
#include "physical-stop-wire.h"
#include "physical-initial-wire.h"
struct wr_iot_rc_physical_intent {unsigned restart,radio_on,reload;};
/* Private RC main-loop API, never a signal handler. Returns1 after claiming
 * the intent, including recoverable preparation failure. step/take must finish
 * that claim; restart additionally requires the verified resume consumer.
 * Does not execute the stock restart or authorize reopen. */
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *);
/* Explicit never-opened origin. Not selected by the normal entry yet; restart
 * stays retained until a typed initial RELEASE consumer completes the owner. */
int wr_iot_rc_physical_begin_initial(const struct wr_iot_rc_physical_intent *);
/* Restart INITIAL with a saved desired request captured under the physical
 * guard before ARM/DOWN. Refusal retains the claimed cleanup path. */
int wr_iot_rc_physical_begin_initial_saved(const struct wr_iot_rc_physical_intent *);
#include "precreated-idle-wire.h"
/* Returns claimed even on post-claim proof refusal; step/take owns cleanup. */
int wr_iot_rc_physical_begin_initial_selected(const struct wr_iot_rc_physical_intent *,
 const unsigned char *,const struct wr_iot_idle_result *);
int wr_iot_rc_physical_begin_initial_off(const struct wr_iot_control_request *);
struct wr_iot_physical_initial_request;
/* Exact ordinary-OFF envelope and completed fence; initial typed receipt only. */
int wr_iot_rc_physical_initial_off_read(const char *,unsigned long long,
 struct wr_iot_physical_initial_request *);

struct wr_iot_physical_initial_request;
int wr_iot_rc_physical_initial_release_read(struct wr_iot_physical_initial_request *);

/* ACTIVE -> existing normal OFF before physical work. Caller provides a fresh
 * private OFF envelope; desired ON settings stay in retained process memory. */
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent *,
 const struct wr_iot_control_request *);
/* Routed normal shutdown only: retained request is claimed under the signal
 * fence; OFF suppresses resume and pending intent does not cancel before ARM.
 * Requires ACTIVE or exact CLOSED backend; INITIAL_OFF is not synthesized.
 * Completion still requires exact off_read RELEASE, then separate PID1 replay. */
int wr_iot_rc_physical_begin_routed_shutdown(const struct wr_iot_control_request *);
enum wr_iot_physical_origin {WR_PHYSICAL_ORIGIN_CLOSE=0,WR_PHYSICAL_ORIGIN_INITIAL=1};
struct wr_iot_rc_physical_resume {
 enum wr_iot_physical_origin origin;
 struct wr_iot_physical_initial_request initial;
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
/* Private non-restart OFF only: exact original envelope, one terminal take.
 * A matching envelope never authorizes reopen or substitutes for completion. */
/* Exact read-only preparation/terminal failure query; no completion grant. */
int wr_iot_rc_physical_off_failed(const char *,unsigned long long);
/* Read the exact acknowledged RELEASE identity before terminal consumption. */
int wr_iot_rc_physical_off_read(const char *,unsigned long long,struct wr_iot_physical_stop_request *);
/* Routed owner only: exact RELEASE, restored unblocked normal-signal mask,
 * retire private receipt, disarm routing and replay original signal to stock.
 * Failed validation/unmask retains the receipt; generic take refuses routed.
 * No PID1 dispatcher/INITIAL_OFF support or automatic route activation here. */
int wr_iot_rc_physical_shutdown_release(const char *,unsigned long long);
/* Optional infallible, bounded PID1-owner retirement after exact completion
 * and successful mask restore, before disarm/replay. No signal/fence mutation,
 * driver calls, allocations or reentry in this cleanup. */
int wr_iot_rc_physical_shutdown_release_cleanup(const char *,unsigned long long,
 void (*)(void *),void *);
int wr_iot_rc_physical_take_off(const char *,unsigned long long);
struct wr_iot_restart_restore;
/* Exact ACTIVE resume consumer; failed proof/mask restore retains ownership.
 * Success retires only old private baseline, never restores the live profile. */
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore *);
struct wr_iot_rc_quiesce;
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore *,const struct wr_iot_rc_quiesce *);
/* Only exact RELEASE with no scheduler/restore owner; normal shutdown only. */
int wr_iot_rc_physical_preresume_cancel(void);
/* Before any session/ARM/Main DOWN; fresh CLOSED and completed quiesce. */
int wr_iot_rc_physical_prearm_cancel(void);
int wr_iot_rc_physical_premain_cancel(struct wr_iot_restart_restore *);
int wr_iot_rc_physical_prehandoff_cancel(struct wr_iot_restart_restore *);
#endif
