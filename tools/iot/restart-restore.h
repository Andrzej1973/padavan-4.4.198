#ifndef WR_IOT_RESTART_RESTORE_H
#define WR_IOT_RESTART_RESTORE_H
#include "restart-guest-controller.h"
#include "restart-services.h"
enum wr_iot_restart_restore_phase {WR_RESTORE_IDLE,WR_RESTORE_PROFILE,WR_RESTORE_MAIN_START,
 WR_RESTORE_MAIN_WAIT,WR_RESTORE_GUEST_BEGIN,WR_RESTORE_GUEST_WAIT,
 WR_RESTORE_SERVICE_BEGIN,WR_RESTORE_SERVICE_WAIT,WR_RESTORE_PREPARED,WR_RESTORE_RETAINED,WR_RESTORE_HANDOFF,WR_RESTORE_FINISHED};
struct wr_iot_restart_restore {
 pid_t owner;int busy;
 unsigned long long handoff_created;
 enum wr_iot_restart_restore_phase phase;
 unsigned char open_id[16];
 struct wr_iot_restart_generation generation;
 struct wr_iot_restart_main main;
 struct wr_iot_restart_guest guest;
 struct wr_iot_restart_services services;
};
/* Zero-initialize at final stable address. Never copy retained contexts.
 * PREPARED is pre-OPEN software preparation only. No baseline/guard release,
 * IoT OPEN, firmware acceptance, or scheduler binding is supplied here. */
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore *,const unsigned char *);
int wr_iot_restart_restore_step(struct wr_iot_restart_restore *);
/* One rebind admission attempt with exact prepared nonce/settings/RELEASE.
 * Keeps baseline and guards on every outcome. No completion/release claim. */
int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore *,const struct wr_iot_control_request *);
/* Fresh exact backend ACTIVE observation after HANDOFF; no profile or guard
 * release, Guest readiness, or physical acceptance implied. */
int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore *);
/* Read-only software completion prerequisites after OPEN. Process presence
 * is not auth readiness, saved profile is not loaded-key/RF acceptance. */
int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore *);
#endif
