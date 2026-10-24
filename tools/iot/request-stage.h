/* Bridge persistent IoT form values into one validated, temporary RC snapshot.
 * Caller must complete bridge teardown first; an existing br-iot is refused.
 * The adapter owns the service guard only for snapshot/staging, not activation. */
#ifndef WR_IOT_REQUEST_STAGE_H
#define WR_IOT_REQUEST_STAGE_H
/* In-memory request adapter for dedicated submission. All reads, validation
 * and staging occur under the same service guard. read() must return borrowed
 * bounded strings for the logical wr_iot_* keys; no candidate NVRAM write is
 * required. The controller still owns snapshot/activation/recovery. */
int wr_iot_request_stage_from(const char *(*read)(void *,const char *),void *context,
 int router_mode,int radio_on,int radio_mode);
int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode);
#endif
