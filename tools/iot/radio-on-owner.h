#ifndef WR_IOT_RADIO_ON_OWNER_H
#define WR_IOT_RADIO_ON_OWNER_H
struct wr_iot_control_request;
/* Private process-context entry, no stock/UI binding. Return1 means owned,
 * including a retained refusal after fence acquisition; never means ON ready. */
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request *,int reload);
int wr_iot_radio_on_pending(void);
/* One child phase per call.1 only terminal software DONE, still owned. */
int wr_iot_radio_on_step(void);
/* Fresh completion/resource proof before wiping private root and exclusion. */
int wr_iot_radio_on_retire(void);
#endif
