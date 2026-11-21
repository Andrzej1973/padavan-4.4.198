/* PCI caller pins adapter, owns teardown and has fenced publication/open.
 * Close only: never unregister/free a child or claim callback/DMA quiescence.
 * Recovery owners must remain live until this stage and their drain finish.
 * A refused/uncertain close retains all allocations for exact-ticket recovery.
 */
static int wr_iot_pci_netdev_preclose(RTMP_ADAPTER *ad, PNET_DEV main_dev)
{
 PNET_DEV devices[WDEV_NUM_MAX+1];
 unsigned long generations[WDEV_NUM_MAX+1];
 unsigned int families[WDEV_NUM_MAX+1];
 unsigned int slot,pass;
 ULONG flags;
 int valid=1,main_found=0;
 if(!ad||!main_dev)return NDIS_STATUS_FAILURE;
 RtmpOSNetDevProtect(1);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!ad->wr_iot_transition.retiring||ad->wr_iot_registration_inflight)valid=0;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++){
  const struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[slot];
  devices[slot]=(PNET_DEV)r->device;generations[slot]=r->generation;families[slot]=r->family;
  if(!r->device){if(r->published||r->removing||r->phase!=WR_REF_IDLE)valid=0;continue;}
  if(!r->generation||!r->published||r->removing||r->removal_stage||
     (r->phase!=WR_REF_IDLE&&r->phase!=WR_REF_OWNED))valid=0;
  if(r->family==WR_REF_FAMILY_MAIN){
   if(r->device!=main_dev||main_found)valid=0;
   main_found=1;
  }else if(r->family!=WR_REF_FAMILY_APCLI&&r->family!=WR_REF_FAMILY_WDS&&
           r->family!=WR_REF_FAMILY_MBSS&&r->family!=WR_REF_FAMILY_MONITOR)valid=0;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!valid||!main_found)goto refused;
 /* All children close first. Main is last, so its last-user stop may run. */
 for(pass=0;pass<2;pass++)for(slot=0;slot<WDEV_NUM_MAX+1;slot++){
  struct wr_iot_interface_ref *r;
  int needs_close;
  if(!devices[slot]||((families[slot]==WR_REF_FAMILY_MAIN)!=(pass==1)))continue;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  r=&ad->wr_iot_interface_refs[slot];
  valid=r->device==devices[slot]&&r->generation==generations[slot]&&
    r->family==families[slot]&&r->published&&!r->removing&&!r->removal_stage;
  needs_close=r->phase==WR_REF_OWNED;
  if(r->phase!=WR_REF_IDLE&&!needs_close)valid=0;
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(!valid)goto refused;
  if(needs_close)RtmpOSNetDevClose(devices[slot]);
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  r=&ad->wr_iot_interface_refs[slot];
  valid=r->device==devices[slot]&&r->generation==generations[slot]&&
    r->family==families[slot]&&r->published&&!r->removing&&
    !r->removal_stage&&r->phase==WR_REF_IDLE;
  if(valid&&!wr_iot_registry_checked_close_terminal(r)){
   const struct wr_iot_family_close *s=&ad->wr_iot_family_close[slot];
   valid=(r->family==WR_REF_FAMILY_APCLI||r->family==WR_REF_FAMILY_MONITOR)&&
     r->close_stage==2&&r->last_token&&r->close_serial&&r->close_epoch&&
     s->phase==WR_FAMILY_CLOSE_DONE&&s->device==r->device&&
     s->generation==r->generation&&s->family==r->family&&
     s->token==r->last_token&&s->serial==r->close_serial&&s->epoch==r->close_epoch;
  }
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(!valid)goto refused;
 }
 /* Last close can mutate shared state: recheck the whole saved identity set. */
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 valid=ad->wr_iot_transition.retiring&&!ad->wr_iot_registration_inflight;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++){
  const struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[slot];
  if(r->device!=devices[slot]||r->generation!=generations[slot]||
     r->family!=families[slot]||r->phase!=WR_REF_IDLE||r->removing||
     r->removal_stage||(devices[slot]&&!r->published))valid=0;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!valid)goto refused;
 RtmpOSNetDevProtect(0);
 return NDIS_STATUS_SUCCESS;
refused:
 RtmpOSNetDevProtect(0);
 return NDIS_STATUS_FAILURE;
}
