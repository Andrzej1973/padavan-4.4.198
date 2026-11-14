#ifndef WR_IOT_RESTART_SERVICE_POLICY_H
#define WR_IOT_RESTART_SERVICE_POLICY_H
struct wr_iot_restart_service_policy {int enterprise,kick_rssi,assoc_rssi;};
enum wr_iot_restart_service_result {WR_SERVICE_NOT_SUBMITTED,WR_SERVICE_UNCERTAIN,WR_SERVICE_RETURNED};
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy *);
/* Process-name liveness only; never process ownership/authentication proof. */
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy *);
/* Fixed slots:0 enterprise daemon if required,1 KickStaRssiLow,2 association
 * threshold. Caller records attempt before invocation; no retry here. Command
 * return does not prove daemon readiness or driver-applied RSSI settings. */
enum wr_iot_restart_service_result wr_iot_rc_restart_service_submit(
 const struct wr_iot_restart_service_policy *,unsigned int);
#endif
