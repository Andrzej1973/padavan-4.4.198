/* Caller serializes access. One write awaits proof per record; RF and MAC
 * keep separate instances of this wire-independent ticket/tuple record.
 * It neither reads hardware nor changes the unconfirmed counter. */
#ifndef WR_IOT_MCU_CONFIG_RF_PENDING_H
#define WR_IOT_MCU_CONFIG_RF_PENDING_H
struct wr_iot_config_rf_pending {
 unsigned int active,poisoned,generation,stream,address,value;
 unsigned long peer_serial,radio_serial,radio_epoch,close_serial,close_epoch;
};
static inline int wr_iot_config_rf_record(struct wr_iot_config_rf_pending *p,
 unsigned long peer,unsigned long radio,unsigned long epoch,
 unsigned long close,unsigned long close_epoch,unsigned int stream,
 unsigned int address,unsigned int value)
{
 if(!p||p->active||p->poisoned||!peer||!radio||!epoch||!close||!close_epoch)return 0;
 if(p->generation==~0U){p->poisoned=1;return 0;}
 p->generation++;p->peer_serial=peer;p->radio_serial=radio;p->radio_epoch=epoch;
 p->close_serial=close;p->close_epoch=close_epoch;
 p->stream=stream;p->address=address;p->value=value;p->active=1;
 return 1;
}
static inline int wr_iot_config_rf_record_matches(const struct wr_iot_config_rf_pending *p,
 unsigned int generation,unsigned long peer,unsigned long radio,unsigned long epoch,
 unsigned long close,unsigned long close_epoch,unsigned int stream,unsigned int address,unsigned int value)
{
 return p&&p->active&&!p->poisoned&&generation&&p->generation==generation&&
  p->peer_serial==peer&&p->radio_serial==radio&&p->radio_epoch==epoch&&
  p->close_serial==close&&p->close_epoch==close_epoch&&p->stream==stream&&
  p->address==address&&p->value==value;
}
#endif
