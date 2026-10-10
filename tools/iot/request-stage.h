/* Bridge persistent IoT form values into one validated, temporary RC snapshot.
 * The caller chooses when to consume the staged snapshot. */
#ifndef WR_IOT_REQUEST_STAGE_H
#define WR_IOT_REQUEST_STAGE_H
int wr_iot_request_stage(int router_mode,int radio_on,int radio_mode);
#endif
