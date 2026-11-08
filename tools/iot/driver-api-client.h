#ifndef WR_IOT_DRIVER_API_CLIENT_H
#define WR_IOT_DRIVER_API_CLIENT_H
#include "driver-api-wire.h"
#include "request.h"
enum wr_iot_driver_submit_result {
 WR_IOT_DRIVER_NOT_SUBMITTED=0,
 WR_IOT_DRIVER_OPEN_COMPLETED=1,
 WR_IOT_DRIVER_OPEN_UNCERTAIN=2
};
/* Caller holds RC service/config ownership. Identity query arms the supplied transaction nonce;
 * OPEN consumes it and revalidates identity. Fixed WR1200JS ra2, no caller-selected remote command. */
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *,const unsigned char *);
/* Any attempted ioctl failure or post-ioctl close failure is UNCERTAIN.
 * OPEN_COMPLETED is not RF/isolation/client acceptance. No automatic retry. */
enum wr_iot_driver_submit_result wr_iot_driver_open_submit(
 const struct wr_iot_driver_open_request *);
/* Bind a copied RC ON request and its lowercase hex transaction ID to a fresh
 * identity observation, then submit OPEN once. Outer backend must separately
 * own network policy, cancellation and recovery; this is not activation. */
enum wr_iot_driver_submit_result wr_iot_driver_open_requested(
 const char *,const struct wr_iot_request *);
/* Original successful ON nonce, not a new OFF transaction ID. Returns only
 * current configuration/close-reference observation. No RF/drain permission;
 * failure clears output and caller must retain isolation/recovery ownership. */
int wr_iot_driver_closed_configuration_read(const unsigned char *,
 struct wr_iot_driver_closed_result *);
#endif
