#ifndef WR_IOT_PROFILE_HISTORY_H
#define WR_IOT_PROFILE_HISTORY_H
#include "restart-profile-receipt.h"
#include "driver-api-wire.h"
enum wr_iot_profile_backend {WR_PROFILE_BACKEND_NONE=0,WR_PROFILE_BACKEND_ACTIVE,
 WR_PROFILE_BACKEND_REBIND_ACTIVE,WR_PROFILE_BACKEND_INITIAL_OFF};
/* Nonsecret identity only. File continuity does not assert loaded credentials,
 * driver ownership or a physical RELEASE. RC reobserves those independently. */
struct wr_iot_profile_binding {
 enum wr_iot_profile_backend kind;char id[33];unsigned long long created;
 struct wr_iot_driver_identity identity;
};
/* RC-private process API. Caller keeps the service guard and lifecycle owner.
 * Publish only at verified completion; read refuses absent/stale/foreign proof.
 * No current desired-key fallback and no borrowed controller pointer. */
int wr_iot_rc_profile_history_remember(const struct wr_iot_profile_binding *,
 const struct wr_iot_restart_profile_receipt *);
int wr_iot_rc_profile_history_read(struct wr_iot_profile_binding *,
 struct wr_iot_restart_profile_receipt *);
#endif
