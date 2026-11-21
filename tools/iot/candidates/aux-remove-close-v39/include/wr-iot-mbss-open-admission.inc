/* Staged wrapper around the reviewed MBSS raw open. No driver-wide safety
 * claim until every close/reset/lifetime entry is bound to the same state. */
#ifndef WR_IOT_MBSS_OBSERVE_MAIN
#include "mt7603-main-observe.h"
#define WR_IOT_MBSS_OBSERVE_MAIN(ad) wr_iot_mt7603_main_config_observed(ad)
#endif
INT MBSS_VirtualIF_Open(PNET_DEV pDev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record=NULL;
 ULONG flags;
 int admitted,ret,observe_iot;
 if(!pDev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(pDev);
 if(!adapter||adapter->net_dev==pDev)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_openable(adapter->wr_iot_interface_refs,
                                     WDEV_NUM_MAX+1,pDev);
 if(!record){
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1;
 }
 observe_iot=IS_MT7603(adapter)&&adapter->ApCfg.BssidNum>=3&&
   (unsigned int)adapter->ApCfg.BssidNum<=sizeof(adapter->ApCfg.MBSSID)/sizeof(adapter->ApCfg.MBSSID[0])&&
   adapter->ApCfg.MBSSID[2].wdev.if_dev==pDev;
 admitted=wr_iot_radio_begin(&adapter->wr_iot_transition,
    adapter->wr_iot_transition.epoch,WR_RADIO_BSS_OPEN,&ticket);
 if(admitted&&!wr_iot_ref_reserve(record,pDev,record->generation,ticket.serial)){
  /* Still under the admission lock: no raw mutation/other intent intervened. */
  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);
  admitted=0;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1;
 /* The ticket excludes participating mutators while the observer takes its
  * own ring lock. Never nest that lock under wr_iot_transition_lock. */
 ret=!observe_iot||WR_IOT_MBSS_OBSERVE_MAIN(adapter);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 if(!ret||adapter->wr_iot_transition.busy!=WR_RADIO_BSS_OPEN||
    adapter->wr_iot_transition.serial!=ticket.serial||
    adapter->wr_iot_transition.epoch!=ticket.epoch||
    adapter->wr_iot_transition.phase!=WR_RADIO_READY||
    !adapter->wr_iot_transition.main_ready||
    adapter->wr_iot_transition.main_inhibited||
    adapter->wr_iot_transition.reset_pending||
    adapter->wr_iot_transition.retiring){
  wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,0);
  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  wake_up_all(&adapter->wr_iot_ticket_wait);
  return -1;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 if(ret==-2){
  /* Abort after MBSS_OPEN was not observed. Keep the module pin and
   * registration blocked; no second open or unregister is safe yet. */
  wr_iot_ref_open_uncertain(record,pDev,record->generation,ticket.serial);
  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  wake_up_all(&adapter->wr_iot_ticket_wait);
  return -1;
 }
 /* Reviewed raw failure branches occur before a successful VIRTUAL_IF_UP;
  * zero return acquired the vendor reference even if CR_ENABLE was unchecked. */
 wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,ret==0);
 /* Existing raw CR_ENABLE does not provide checked hardware success.
  * Keep readiness unverified rather than accepting its zero return as proof. */
 if(ret==0)wr_iot_radio_finish_unverified(&adapter->wr_iot_transition,&ticket);
 else wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 return ret;
}
