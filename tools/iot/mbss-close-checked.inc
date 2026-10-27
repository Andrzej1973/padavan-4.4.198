/* Candidate: sole owner of CLOSE/BSS_CLOSE ticket pins all lifetimes.
 * Not an ndo_stop replacement: failure requires retained-resource continuation. */
/* The caller pins adapter/netdev lifetime. Count, registration and radio
 * ticket are observed under one adapter lock; retry uses the same generation
 * and ticket, never another begin. */
INT wr_iot_mbss_begin_close(PNET_DEV dev,struct wr_iot_radio_ticket *ticket,
                            unsigned long *generation)
{
 PRTMP_ADAPTER ad;
 struct wr_iot_interface_ref *r;
 ULONG flags;
 if(!dev||!ticket||!generation)return -1;
 *generation=0;
 ad=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!ad||ad->net_dev==dev)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 r=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 if(!r||r->family!=WR_REF_FAMILY_MBSS||
    !wr_iot_registry_count_matches(ad->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad))||
    !wr_iot_radio_begin_stop(&ad->wr_iot_transition,
                                VIRTUAL_IF_NUM(ad),ticket)){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 /* Preserve the admitted ticket before any unlocked vendor close work. A
  * recovery worker must use this provenance, never reconstruct prior state
  * from the radio's possibly changed epoch or phase. */
 r->close_epoch=ticket->epoch;
 r->close_vendor_count=VIRTUAL_IF_NUM(ad);
 r->close_prior_phase=(int)ticket->prior_phase;
 r->close_prior_ready=ticket->prior_ready;
 *generation=r->generation;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return 0;
}
/* Caller holds the common adapter lock. A vendor call can run unlocked, so
 * revalidate the exact registration and ticket before writing its next stage. */
static inline int wr_iot_mbss_close_record_current(PRTMP_ADAPTER ad,
 struct wr_iot_interface_ref *r,PNET_DEV dev,unsigned long generation,
 unsigned long token,const struct wr_iot_radio_ticket *ticket)
{
 return wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
                             dev,generation)==r&&r->published&&
        wr_iot_ref_matches(r,dev,generation,token)&&
        r->phase==WR_REF_CLOSING&&r->close_running&&
        r->close_serial==ticket->serial&&
        r->close_epoch==ticket->epoch&&
        !ticket->reset_kind&&
        ((ticket->operation==WR_RADIO_CLOSE&&r->close_vendor_count==1U)||
         (ticket->operation==WR_RADIO_BSS_CLOSE&&
          r->close_vendor_count>1U))&&
        r->close_prior_phase==(int)ticket->prior_phase&&
        r->close_prior_ready==ticket->prior_ready&&
        ad->wr_iot_transition.busy==ticket->operation&&
        ad->wr_iot_transition.serial==ticket->serial;
}
/* Caller holds the adapter lock. An invalidated/reused slot must never have
 * its next generation's executor flag cleared by an old close. */
static inline void wr_iot_mbss_close_release_locked(PRTMP_ADAPTER ad,
 struct wr_iot_interface_ref *r,PNET_DEV dev,unsigned long generation,
 unsigned long token,const struct wr_iot_radio_ticket *ticket)
{
 if(wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
                         dev,generation)==r&&
    wr_iot_ref_matches(r,dev,generation,token)&&
    r->close_serial==ticket->serial)
  r->close_running=0;
}
static inline INT wr_iot_mbss_close_fail(PRTMP_ADAPTER ad,
 struct wr_iot_interface_ref *r,PNET_DEV dev,unsigned long generation,
 unsigned long token,const struct wr_iot_radio_ticket *ticket)
{
 ULONG flags;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return -1;
}
/* The closing record still owns its pre-DOWN reference until the checked
 * completion. All other live records must be stable OWNED references, and
 * their count must equal the vendor count after this BSS was decremented. */
static inline int wr_iot_mbss_count_after_down(PRTMP_ADAPTER ad,
 const struct wr_iot_interface_ref *closing)
{
 unsigned int i,others=0;
 for(i=0;i<WDEV_NUM_MAX+1;i++){
  const struct wr_iot_interface_ref *ref=&ad->wr_iot_interface_refs[i];
  if(ref==closing)continue;
  if(ref->phase==WR_REF_IDLE)continue;
  if(ref->phase!=WR_REF_OWNED||!ref->device||!ref->generation||
     !ref->last_token||!ref->published||ref->removing)return 0;
  others++;
 }
 return VIRTUAL_IF_NUM(ad)==others;
}
INT wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long generation,
                              const struct wr_iot_radio_ticket *ticket)
{
 PRTMP_ADAPTER ad;
 struct wr_iot_interface_ref *r=NULL;
 unsigned long token;
 unsigned int stage;
#ifdef MT_MAC
 INT bss_id;
#endif
 ULONG flags;
 int ret;
 if(!dev||!generation||!ticket)return -1;
 ad=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!ad||ad->net_dev==dev)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ticket->operation!=WR_RADIO_CLOSE&&ticket->operation!=WR_RADIO_BSS_CLOSE){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 r=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
                        dev,generation);
 if(!r||!r->published){RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;}
 if(!r->close_epoch||r->close_epoch!=ticket->epoch||
    ticket->reset_kind||
    !((ticket->operation==WR_RADIO_CLOSE&&r->close_vendor_count==1U)||
      (ticket->operation==WR_RADIO_BSS_CLOSE&&
       r->close_vendor_count>1U))||
    r->close_prior_phase!=(int)ticket->prior_phase||
    r->close_prior_ready!=ticket->prior_ready){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 if(r->phase==WR_REF_IDLE&&r->close_stage==4U&&
    r->close_serial==ticket->serial&&
    ad->wr_iot_transition.retired_serial==ticket->serial){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return 0;
 }
 if(ad->wr_iot_transition.busy!=ticket->operation||
    ad->wr_iot_transition.serial!=ticket->serial){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 if(r->phase==WR_REF_OWNED){
  if(!wr_iot_ref_begin_close(r,dev,r->generation,r->last_token)){
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
  }
  r->close_serial=ticket->serial;r->close_stage=0;
 }
 if(r->close_serial!=ticket->serial||r->close_running||
    (r->phase!=WR_REF_CLOSING&&!(r->phase==WR_REF_IDLE&&r->close_stage==4U))){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 token=r->last_token;
 stage=r->close_stage;
 if(stage==4U||stage>4U){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  return stage==4U?0:-1;
 }
 r->close_running=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(stage==0U){
#ifdef MT_MAC
  ret=RTMP_AP_IoctlHandle(ad,NULL,CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE,0,dev,0);
  if(ret!=NDIS_STATUS_SUCCESS)goto uncertain;
#endif
  RTMP_OS_NETDEV_STOP_QUEUE(dev);
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  if(!wr_iot_mbss_close_record_current(ad,r,dev,generation,token,ticket)){
   wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
  }
  r->close_stage=1U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
 if(stage<=1U){
  /* Direct checked result; legacy ioctl dispatch discarded MBSS_Close status. */
  if(MBSS_Close(dev)!=0)goto uncertain;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  if(!wr_iot_mbss_close_record_current(ad,r,dev,generation,token,ticket)){
   wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
  }
  r->close_stage=2U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
#ifdef MT_MAC
 /* A released TxS PID may still own an in-flight beacon callback. This
  * snapshot can delay close, but cannot prove that no late report exists. */
 bss_id=RT28xx_MBSS_IdxGet(ad,dev);
 if(bss_id<=0||bss_id>=ad->ApCfg.BssidNum||bss_id>=MAX_MBSSID_NUM(ad))
  goto uncertain;
#ifdef RTMP_PCI_SUPPORT
 /* Snapshot the target's pending beacon DMA cells before virtual down.
  * This can delay close; it cannot prove that no late TxS will arrive. */
 ret=WrBeaconDmaOutstanding(ad,(UINT32)bss_id);
 if(ret<0)goto uncertain;
 if(ret>0)return wr_iot_mbss_close_fail(ad,r,dev,generation,token,ticket);
#endif
 ret=WrBeaconTxSOutstanding(ad,(UINT32)bss_id);
 if(ret<0)goto uncertain;
 if(ret>0)return wr_iot_mbss_close_fail(ad,r,dev,generation,token,ticket); /* Retain stage 2/ticket. */
#endif
 if(stage<=2U){
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
  RT_MOD_HNAT_DEREG(dev);
#endif
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  if(!wr_iot_mbss_close_record_current(ad,r,dev,generation,token,ticket)){
   wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
  }
  r->close_stage=3U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
 ret=wr_iot_virtual_down_checked(ad,ticket);
 if(ret!=NDIS_STATUS_SUCCESS)
  return wr_iot_mbss_close_fail(ad,r,dev,generation,token,ticket);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_mbss_close_record_current(ad,r,dev,generation,token,ticket)){
  wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 /* Retire the ticket only when the reference can be consumed under this
  * same lock. A failed consume after retirement would strand the module pin
  * without a live close ticket for the retained recovery owner. */
 if(!wr_iot_ref_matches(r,dev,generation,token)||
    r->phase!=WR_REF_CLOSING||
    !wr_iot_mbss_count_after_down(ad,r)){
  wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 if(!wr_iot_radio_finish(&ad->wr_iot_transition,ticket,1)){
  wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 if(!wr_iot_ref_consume(r,dev,generation,token)){
  wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 r->close_stage=4U;
 wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 wake_up_all(&ad->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
uncertain:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_mbss_close_record_current(ad,r,dev,generation,token,ticket)){
  wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 r->close_stage=5U;
 wr_iot_mbss_close_release_locked(ad,r,dev,generation,token,ticket);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return -1;
}
