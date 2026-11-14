#ifndef WR_IOT_RC_BACKEND_H
#define WR_IOT_RC_BACKEND_H
#include "control-record.h"
struct wr_iot_rc_mode {int router,radio,mode;};
/* Strong RC read-only adapter. Caller holds service guard; exactly1 means the
 * three fields were read. It does not generate profiles or restart a radio. */
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *);
/* RC-process-only endpoint. HTTPD must request this over authenticated private
 * IPC, never call a separately linked copy of the process-local owner. */
int wr_iot_rc_backend_observed(const struct wr_iot_control_result *);
struct wr_iot_driver_closed_result;
/* Fresh software CLOSE from the private retained OFF owner, never mailbox-only. */
int wr_iot_rc_backend_closed(struct wr_iot_driver_closed_result *);
#endif
