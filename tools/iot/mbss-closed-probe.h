/* Caller holds transition lock for begin/finish, pins adapter/netdev lifetime
 * across unlocked configuration observation, and wakes waiters after retirement.
 * This is not an RF/FIFO/late-callback receipt or isolation-release permission. */
#ifndef WR_IOT_MBSS_CLOSED_PROBE_H
#define WR_IOT_MBSS_CLOSED_PROBE_H
#include "radio-transition-api.h"
#include "mbss-close-receipt.h"
struct wr_iot_mbss_closed_probe {
 struct wr_iot_radio_ticket ticket;
 const void *main_device,*iot_device;
 unsigned long generation,open_token,close_serial;
 unsigned int active;
};
static inline int wr_iot_mbss_closed_probe_begin(struct wr_iot_mbss_closed_probe *p,
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned long open_token,unsigned long close_serial,
 unsigned int vendor_count){
 if(!p||p->active||!wr_iot_mbss_closed_reference(radio,slots,count,main_dev,iot_dev,
    generation,open_token,close_serial,vendor_count))return 0;
 if(!wr_iot_radio_begin(radio,radio->epoch,WR_RADIO_BSS_OBSERVE,&p->ticket))return 0;
 p->main_device=main_dev;p->iot_device=iot_dev;p->generation=generation;
 p->open_token=open_token;p->close_serial=close_serial;p->active=1;return 1;
}
static inline int wr_iot_mbss_closed_probe_finish(struct wr_iot_mbss_closed_probe *p,
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,unsigned int vendor_count,int observed){
 int accepted;
 if(!p||!p->active||!radio)return 0;
 accepted=observed==1&&radio->busy==WR_RADIO_BSS_OBSERVE&&
  radio->serial==p->ticket.serial&&radio->epoch==p->ticket.epoch&&
  wr_iot_mbss_closed_record_current(radio,slots,count,p->main_device,p->iot_device,
   p->generation,p->open_token,p->close_serial,vendor_count);
 if(!wr_iot_radio_bss_observe_end(radio,&p->ticket))return 0;
 p->active=0;return accepted;
}
#endif
