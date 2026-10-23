/* Staged wrapper around the reviewed MBSS raw open. No driver-wide safety
 * claim until every close/reset/lifetime entry is bound to the same state. */
INT MBSS_VirtualIF_Open(PNET_DEV pDev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record=NULL;
 unsigned int slot;
 ULONG flags;
 int admitted,ret;
 if(!pDev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(pDev);
 if(!adapter||adapter->net_dev==pDev)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++)
  if(adapter->wr_iot_interface_refs[slot].device==pDev){record=&adapter->wr_iot_interface_refs[slot];break;}
 if(!record||!record->published||record->removing||record->phase!=WR_REF_IDLE){
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1;
 }
 admitted=wr_iot_radio_begin(&adapter->wr_iot_transition,
    adapter->wr_iot_transition.epoch,WR_RADIO_BSS_OPEN,&ticket);
 if(admitted&&!wr_iot_ref_reserve(record,pDev,record->generation,ticket.serial)){
  /* Still under the admission lock: no raw mutation/other intent intervened. */
  adapter->wr_iot_transition.busy=0;
  admitted=0;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1;
 ret=wr_iot_mbss_open_raw(pDev);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* Reviewed raw failure branches occur before a successful VIRTUAL_IF_UP;
  * zero return acquired the vendor reference even if CR_ENABLE was unchecked. */
 wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,ret==0);
 /* Existing raw CR_ENABLE does not provide checked hardware success.
  * Keep readiness unverified rather than accepting its zero return as proof. */
 if(ret==0)wr_iot_radio_finish_unverified(&adapter->wr_iot_transition,&ticket);
 else wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 return ret;
}
