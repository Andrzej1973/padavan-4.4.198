/* Bridge persistent IoT form values into one validated, temporary RC snapshot.
 * Caller must complete bridge teardown first; an existing br-iot is refused.
 * The adapter owns the service guard only for snapshot/staging, not activation. */
#ifndef WR_IOT_REQUEST_STAGE_H
#define WR_IOT_REQUEST_STAGE_H
int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode);
#endif
