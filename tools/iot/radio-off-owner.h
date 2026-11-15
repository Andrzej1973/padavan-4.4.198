#ifndef WR_IOT_RADIO_OFF_OWNER_H
#define WR_IOT_RADIO_OFF_OWNER_H
#include <sys/types.h>
#include "control-record.h"
/* Private RC state. Zero initialize; never copy a live owner. Terminal result
 * must be acknowledged before admitting another OFF. No radio/UI binding. */
struct wr_iot_radio_off_owner {pid_t owner;char id[33];unsigned long long created;int result,busy;};
int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner *,const struct wr_iot_control_request *);
int wr_iot_radio_off_poll(struct wr_iot_radio_off_owner *);
int wr_iot_radio_off_take(struct wr_iot_radio_off_owner *);
#endif
