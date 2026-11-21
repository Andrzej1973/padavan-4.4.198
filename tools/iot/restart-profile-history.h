#ifndef WR_IOT_RESTART_PROFILE_HISTORY_H
#define WR_IOT_RESTART_PROFILE_HISTORY_H
#include "profile-history.h"
#include "initial-off.h"
struct wr_iot_restart_restore;
/* Inert preflight output owned by the physical finish transaction. No live
 * controller, allocated bytes or borrowed credential pointer. */
struct wr_iot_restart_profile_history {
 struct wr_iot_profile_binding binding;
 struct wr_iot_restart_profile_receipt profile;
 struct wr_iot_initial_off idle;
};
int wr_iot_rc_restart_profile_prepare(struct wr_iot_restart_restore *,
 struct wr_iot_restart_profile_history *);
/* Only successful outer fence cleanup may commit a prepared output. */
void wr_iot_rc_restart_profile_commit(const struct wr_iot_restart_profile_history *);
#endif
