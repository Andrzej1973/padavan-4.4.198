/* Candidate normal-OFF composition. Outer activation controller holds its
 * service guard and performs radio QUIESCE, quarantine, bridge teardown and
 * final observed RF/main/guest/service readiness. No driver binding here. */
#ifndef WR_IOT_DISABLE_CONTROLLER_H
#define WR_IOT_DISABLE_CONTROLLER_H
#include "disable-services.h"
#include "radio-profile-state.h"
struct wr_iot_disable_controller {
 struct wr_iot_disable_services services;
 struct wr_iot_radio_profile_state radio;
 int profile_committed;
};
/* Read-only fresh capture for DISABLE_SNAPSHOT; zero initialize context. */
int wr_iot_disable_begin(struct wr_iot_disable_controller *);
/* DISABLE_SERVICES: BSS closed/quarantined, owned bridge still exists. */
int wr_iot_disable_apply_services(struct wr_iot_disable_controller *);
/* DISABLE_APPLY after bridge teardown: remove exact owned profile entries. */
int wr_iot_disable_apply_profile(struct wr_iot_disable_controller *);
/* DISABLE_COMMIT only AFTER the outer final observation and guard removal.
 * Receipt tracks partial release so a retry never restores an old profile.
 * This API cannot itself establish RF/main/guest health. */
int wr_iot_disable_commit(struct wr_iot_disable_controller *);
#endif
