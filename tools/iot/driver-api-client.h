#ifndef WR_IOT_DRIVER_API_CLIENT_H
#define WR_IOT_DRIVER_API_CLIENT_H
#include "driver-api-wire.h"
enum wr_iot_driver_submit_result {
 WR_IOT_DRIVER_NOT_SUBMITTED=0,
 WR_IOT_DRIVER_OPEN_COMPLETED=1,
 WR_IOT_DRIVER_OPEN_UNCERTAIN=2
};
/* Caller holds RC service/config ownership. Identity is an observation only;
 * OPEN revalidates it. Fixed WR1200JS ra2, no caller-selected remote command. */
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *);
/* Any attempted ioctl failure or post-ioctl close failure is UNCERTAIN.
 * OPEN_COMPLETED is not RF/isolation/client acceptance. No automatic retry. */
enum wr_iot_driver_submit_result wr_iot_driver_open_submit(
 const struct wr_iot_driver_open_request *);
#endif
