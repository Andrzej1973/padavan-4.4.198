/* Persistent software observation owner. Begin/finish require transition lock;
 * caller pins adapter/netdev and holds RTNL across unlocked hardware readback.
 * Unretirable ticket retains active context: caller must not discard it.
 * Acceptance is initial idle configuration only, never RF or future permission. */
#ifndef WR_IOT_PRECREATED_IDLE_PROBE_H
#define WR_IOT_PRECREATED_IDLE_PROBE_H
#include "precreated-idle-reference.h"
struct wr_iot_precreated_idle_probe {
 struct wr_iot_radio_ticket ticket;
 const void *main_device,*iot_device;
 unsigned long generation;
 unsigned int active,accepted;
};
static inline int wr_iot_precreated_idle_probe_begin(
 struct wr_iot_precreated_idle_probe *p,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *main_dev,
 const void *iot_dev,unsigned long generation,unsigned int vendor_count)
{
 if(!p||p->active||!wr_iot_precreated_idle_reference(radio,slots,count,
    main_dev,iot_dev,generation,vendor_count))return 0;
 if(!wr_iot_radio_begin(radio,radio->epoch,WR_RADIO_BSS_OBSERVE,&p->ticket))return 0;
 p->main_device=main_dev;p->iot_device=iot_dev;p->generation=generation;
 p->accepted=0;p->active=1;return 1;
}
static inline int wr_iot_precreated_idle_probe_finish(
 struct wr_iot_precreated_idle_probe *p,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,unsigned int vendor_count,
 int observed)
{
 struct wr_iot_radio_transition snapshot;int accepted;
 if(!p||!p->active||!radio)return 0;
 /* Only our exact observation may be ignored in the local idle predicate.
  * Stored radio state is never made temporarily idle during validation. */
 if(radio->busy!=WR_RADIO_BSS_OBSERVE||radio->serial!=p->ticket.serial||
    p->ticket.operation!=WR_RADIO_BSS_OBSERVE||p->ticket.reset_kind)return 0;
 snapshot=*radio;snapshot.busy=0;
 accepted=observed==1&&radio->epoch==p->ticket.epoch&&
  wr_iot_precreated_idle_reference(&snapshot,slots,count,p->main_device,
   p->iot_device,p->generation,vendor_count);
 if(!wr_iot_radio_bss_observe_end(radio,&p->ticket))return 0;
 p->active=0;p->accepted=accepted;return accepted;
}
/* Locked reply preflight. A failed observation may retire its ticket too;
 * therefore retired_serial alone must never be interpreted as acceptance. */
static inline int wr_iot_precreated_idle_probe_current(
 const struct wr_iot_precreated_idle_probe *p,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned int vendor_count)
{
 return p&&radio&&!p->active&&p->accepted==1&&p->main_device==main_dev&&
  p->iot_device==iot_dev&&p->generation==generation&&p->ticket.serial&&
  p->ticket.operation==WR_RADIO_BSS_OBSERVE&&!p->ticket.reset_kind&&
  p->ticket.epoch==radio->epoch&&radio->serial==p->ticket.serial&&
  radio->retired_serial==p->ticket.serial&&
  wr_iot_precreated_idle_reference(radio,slots,count,main_dev,iot_dev,
    generation,vendor_count);
}
#endif
