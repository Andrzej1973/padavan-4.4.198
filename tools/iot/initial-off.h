/* Initial never-opened OFF observation, not CLOSE or RF retirement proof.
 * Zero initialize once; retains only nonsecret transaction/driver identity. */
#ifndef WR_IOT_INITIAL_OFF_H
#define WR_IOT_INITIAL_OFF_H
#include <sys/types.h>
#include "control-record.h"
#include "precreated-idle-wire.h"
#include "physical-stop-wire.h"
#include "physical-initial-wire.h"
struct wr_iot_initial_off {
 pid_t owner;
 char id[33];unsigned long long created;
 unsigned char nonce[16];
 struct wr_iot_idle_result idle;
 int ready;
};
/* Fresh Main READY plus still-never-opened ra2 after typed initial RELEASE.
 * Caller holds service/shutdown admission; no UP, generation or cleanup. */
int wr_iot_initial_main_current(const struct wr_iot_physical_initial_request *,
 const unsigned char *,struct wr_iot_driver_identity *);
/* Read-only postrelease observer under a temporary service guard. Expected
 * Main identity is retained by the completed owner; never grants reopen. */
int wr_iot_initial_postrelease_current(const struct wr_iot_physical_initial_request *,
 const unsigned char *,const struct wr_iot_driver_identity *);
struct wr_iot_initial_shutdown_owner;
int wr_iot_initial_off_begin_shutdown(struct wr_iot_initial_off *,const struct wr_iot_control_request *,const struct wr_iot_initial_shutdown_owner *);
int wr_iot_initial_off_request_shutdown(const struct wr_iot_initial_off *,const unsigned char *,struct wr_iot_physical_initial_request *,const struct wr_iot_initial_shutdown_owner *);
int wr_iot_initial_off_begin(struct wr_iot_initial_off *,const struct wr_iot_control_request *);
/* Caller holds service guard; read-only current observation for same owner. */
int wr_iot_initial_off_observed(const struct wr_iot_initial_off *);
/* Fresh observation becomes an ARM request only; no physical completion lease. */
int wr_iot_initial_off_physical_request(const struct wr_iot_initial_off *,
 const unsigned char *,struct wr_iot_physical_initial_request *);
/* Read-only relationship check after Main restart: caller separately owns and
 * verifies RELEASE and new Main identity. No cleanup/OPEN/RF permission. */
int wr_iot_initial_off_restarted_observed(const struct wr_iot_initial_off *,
 const struct wr_iot_physical_stop_request *,const struct wr_iot_driver_identity *);
#endif
