#ifndef WR_IOT_DRIVER_API_CLIENT_H
#define WR_IOT_DRIVER_API_CLIENT_H
#include "driver-api-wire.h"
#include "request.h"
#include "driver-api-open-current-wire.h"
#include "driver-api-open-recovery-wire.h"
#include "driver-api-close-progress-wire.h"
#include "driver-api-close-release-wire.h"
enum wr_iot_driver_submit_result {
 WR_IOT_DRIVER_NOT_SUBMITTED=0,
 WR_IOT_DRIVER_OPEN_COMPLETED=1,
 WR_IOT_DRIVER_OPEN_UNCERTAIN=2
};
/* Caller holds RC service/config ownership. Identity query arms the supplied transaction nonce;
 * OPEN consumes it and revalidates identity. Fixed WR1200JS ra2, no caller-selected remote command. */
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *,const unsigned char *);
/* Any attempted ioctl failure or post-ioctl close failure is UNCERTAIN.
 * OPEN_COMPLETED additionally requires exact current-OPEN receipt readback
 * after the syscall. It is not RF/isolation/client acceptance. No retry. */
enum wr_iot_driver_submit_result wr_iot_driver_open_submit(
 const struct wr_iot_driver_open_request *);
/* Bind a copied RC ON request and its lowercase hex transaction ID to a fresh
 * identity observation, then submit OPEN once. Outer backend must separately
 * own network policy, cancellation and recovery; this is not activation. */
enum wr_iot_driver_submit_result wr_iot_driver_open_requested(
 const char *,const struct wr_iot_request *);
/* Caller supplies a unique nonce per attempt and retains this under its
 * serialized service owner until recovery completes. Never reuse an ON nonce.
 * Retained nonsecret identity for recovery of this exact attempted OPEN.
 * NOT_SUBMITTED clears it; UNCERTAIN retains it, never a rollback permission. */
struct wr_iot_driver_attempt {
 struct wr_iot_driver_identity identity;
 unsigned char request_id[16];
};
enum wr_iot_driver_submit_result wr_iot_driver_open_requested_tracked(
 const char *,const struct wr_iot_request *,struct wr_iot_driver_attempt *);
/* Match refusal against the original attempted identity, not a fresh query. */
int wr_iot_driver_attempt_refused(const struct wr_iot_driver_attempt *);
/* Current configuration-only CLOSED bound to retained successful ON identity.
 * Neither this nor historical refusal authorizes isolation release. */
int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *,
 struct wr_iot_driver_closed_result *);
/* Original successful ON nonce, not a new OFF transaction ID. Returns only
 * current configuration/close-reference observation. No RF/drain permission;
 * failure clears output and caller must retain isolation/recovery ownership. */
int wr_iot_driver_closed_configuration_read(const unsigned char *,
 struct wr_iot_driver_closed_result *);
/* Historical pre-mutation refusal only. Does not authorize network rollback. */
int wr_iot_driver_refusal_read(const unsigned char *,struct wr_iot_driver_refusal_result *);
/* Diagnostic only: never authorizes retry, rollback or isolation release. */
int wr_iot_driver_uncertain_read(const struct wr_iot_driver_attempt *,struct wr_iot_driver_uncertain_result *);
/* Current owned-reference snapshot only. Caller retains original OPEN attempt;
 * a subsequent CLOSE must revalidate token/identity, not rely on this as lease. */
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *,
 struct wr_iot_driver_open_current_result *);
/* Fixed ra2 CLOSE transport. Input must retain the successful OPEN nonce,
 * epoch, generation and token under the serialized controller owner.
 * No automatic CLOSE retry. Progress advances the same retained operation.
 * CALL_COMPLETED proves kernel-call completion only. Isolation and the OPEN
 * fence remain owned until the separate lifecycle completion checks pass. */
enum wr_iot_driver_close_submit_result {
 WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED=0,
 WR_IOT_DRIVER_CLOSE_CALL_COMPLETED=1,
 WR_IOT_DRIVER_CLOSE_PENDING=2,
 WR_IOT_DRIVER_CLOSE_UNCERTAIN=3
};
/* Recovery-only configuration token; never evidence that ON completed.
 * Normal open_submit retains the separate first-publication query. */
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt *,
 struct wr_iot_driver_open_recovery_result *);
/* Construct CLOSE identity from the retained OPEN attempt and its observed
 * current receipt. No ioctl or ownership transfer occurs in this helper. */
int wr_iot_driver_close_request_from_open(struct wr_iot_driver_close_request *,
 const struct wr_iot_driver_attempt *,const struct wr_iot_driver_open_current_result *);
enum wr_iot_driver_close_submit_result wr_iot_driver_close_submit(
 const struct wr_iot_driver_close_request *);
enum wr_iot_driver_close_submit_result wr_iot_driver_close_progress_submit(
 const struct wr_iot_driver_close_request *);
/* Experimental no-host driver only. Success releases software CLOSE owner;
 * network policy and runtime acceptance remain with the activation backend. */
enum wr_iot_driver_close_submit_result wr_iot_driver_close_release_submit(
 const struct wr_iot_driver_close_request *);
#endif
