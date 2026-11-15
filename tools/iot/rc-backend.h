#ifndef WR_IOT_RC_BACKEND_H
#define WR_IOT_RC_BACKEND_H
/* Read-only PID1 bootstrap eligibility, not driver/network readiness. */
int wr_iot_rc_boot_idle(void);
struct wr_iot_control_result;
struct wr_iot_rc_mode {int router,radio,mode;};
/* Strong RC read-only adapter. Caller holds service guard; exactly1 means the
 * three fields were read. It does not generate profiles or restart a radio. */
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *);
/* Saved ON policy only for physical OFF-to-ON admission. Does not assert live
 * radio UP; caller must separately prove physical DOWN/new Main ownership. */
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *);
/* RC-process-only endpoint. HTTPD must request this over authenticated private
 * IPC, never call a separately linked copy of the process-local owner. */
int wr_iot_rc_backend_observed(const struct wr_iot_control_result *);
struct wr_iot_driver_closed_result;
/* Fresh software CLOSE from the private retained OFF owner, never mailbox-only. */
int wr_iot_rc_backend_closed(struct wr_iot_driver_closed_result *);
struct wr_iot_initial_off;
struct wr_iot_physical_initial_request;
/* Fresh never-opened observation for physical ARM; caller retains witness and
 * service/shutdown admission. Never returns a legacy CLOSE certificate. */
int wr_iot_rc_backend_initial_request(const struct wr_iot_initial_off *,
 const unsigned char *,struct wr_iot_physical_initial_request *);
/* Retained successful prepare_radio_stop witness, reobserved at each call.
 * Failed preparation never publishes a partially initialized replacement. */
int wr_iot_rc_backend_prepared_initial_request(const unsigned char *,
 struct wr_iot_physical_initial_request *);
struct wr_iot_request;
/* Caller holds service/config guard; copied stable saved ON/OFF intent. */
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request *);
struct wr_iot_control_request;
struct wr_iot_physical_stop_request;
/* Private resume admission: exact retained old OFF/physical RELEASE tuple,
 * fresh new-Main checks inside runner, stable owner; caller keeps outer guards. */
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request *,
 const struct wr_iot_physical_stop_request *);
struct wr_iot_driver_identity;
/* Exact private ACTIVE rebind owner, not generic APPLIED/OFF status. */
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request *,
 const struct wr_iot_physical_stop_request *,const struct wr_iot_driver_identity *);
struct wr_iot_rc_quiesce;
/* Shutdown-only fresh CLOSED for this exact ON/physical/identity and OFF owner. */
int wr_iot_rc_rebind_shutdown_closed(const struct wr_iot_control_result *,
 const struct wr_iot_physical_stop_request *,const struct wr_iot_driver_identity *,
 const struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
/* Completed pre-OPEN rejection only; not an OFF/CLOSED token or reopen lease. */
int wr_iot_rc_rebind_preopen_rejected(const struct wr_iot_control_result *,
 const struct wr_iot_physical_stop_request *,const struct wr_iot_driver_identity *);
#endif
