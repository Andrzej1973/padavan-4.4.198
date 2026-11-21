/* Stage form values into a validated temporary RC snapshot. Staging requires
 * bridge teardown first and refuses an existing br-iot. The read-only matcher
 * below checks an already prepared activation under its outer service guard.
 * This adapter does not own the complete activation/recovery lifecycle. */
#ifndef WR_IOT_REQUEST_STAGE_H
#define WR_IOT_REQUEST_STAGE_H
/* In-memory request adapter for dedicated submission. All reads, validation
 * and staging occur under the same service guard. read() must return borrowed
 * bounded strings for the logical wr_iot_* keys; no candidate NVRAM write is
 * required. The controller still owns snapshot/activation/recovery. */
int wr_iot_request_stage_from(const char *(*read)(void *,const char *),void *context,
 int router_mode,int radio_on,int radio_mode);
int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode);
struct wr_iot_request;
/* Read-only exact staged request/gate observation for serialized startup. */
int wr_iot_request_prepared_matches(const struct wr_iot_request *,int,int);
/* Read-only under the current service guard, requires all three ready gates
 * and exact staged credential/subnet values. Not loaded-driver acceptance. */
int wr_iot_request_stage_matches(const struct wr_iot_request *);
/* Enable DHCP/DNS candidate generation only after owned bridge/address and
 * route checks. ra2 stays DOWN, firewall gate stays0. Caller retains startup
 * snapshot/guard on any failure, including a possibly partial gate write. */
int wr_iot_request_network_enable(const struct wr_iot_request *);
#endif
