/* Candidate: sole owner of CLOSE/BSS_CLOSE ticket pins all lifetimes.
 * Not an ndo_stop replacement: failure requires retained-resource continuation. */
INT wr_iot_mbss_close_checked(PNET_DEV dev,const struct wr_iot_radio_ticket *ticket)
{
 PRTMP_ADAPTER ad;
 struct wr_iot_interface_ref *r=NULL;
 unsigned int i,stage;
#ifdef MT_MAC
 INT bss_id;
#endif
 ULONG flags;
 int ret;
 if(!dev||!ticket)return -1;
 ad=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!ad||ad->net_dev==dev)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if((ticket->operation!=WR_RADIO_CLOSE&&ticket->operation!=WR_RADIO_BSS_CLOSE)||
    ad->wr_iot_transition.busy!=ticket->operation||ad->wr_iot_transition.serial!=ticket->serial){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 for(i=0;i<WDEV_NUM_MAX+1;i++)if(ad->wr_iot_interface_refs[i].device==dev){r=&ad->wr_iot_interface_refs[i];break;}
 if(!r||!r->published){RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;}
 if(r->phase==WR_REF_OWNED){
  if(!wr_iot_ref_begin_close(r,dev,r->generation,r->last_token)){
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
  }
  r->close_serial=ticket->serial;r->close_stage=0;
 }
 if(r->close_serial!=ticket->serial||
    (r->phase!=WR_REF_CLOSING&&!(r->phase==WR_REF_IDLE&&r->close_stage==4U))){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 stage=r->close_stage;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(stage==4U)return 0;
 if(stage>4U)return -1;
 if(stage==0U){
#ifdef MT_MAC
  ret=RTMP_AP_IoctlHandle(ad,NULL,CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE,0,dev,0);
  if(ret!=NDIS_STATUS_SUCCESS)goto uncertain;
#endif
  RTMP_OS_NETDEV_STOP_QUEUE(dev);
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);r->close_stage=1U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
 if(stage<=1U){
  /* Direct checked result; legacy ioctl dispatch discarded MBSS_Close status. */
  if(MBSS_Close(dev)!=0)goto uncertain;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);r->close_stage=2U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
#ifdef MT_MAC
 /* A released TxS PID may still own an in-flight beacon callback. This
  * snapshot can delay close, but cannot prove that no late report exists. */
 bss_id=RT28xx_MBSS_IdxGet(ad,dev);
 if(bss_id<=0||bss_id>=ad->ApCfg.BssidNum||bss_id>=MAX_MBSSID_NUM(ad))
  goto uncertain;
 ret=WrBeaconTxSOutstanding(ad,(UINT32)bss_id);
 if(ret<0)goto uncertain;
 if(ret>0)return -1; /* Retain stage 2/ticket; the owner may retry. */
#endif
 if(stage<=2U){
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
  RT_MOD_HNAT_DEREG(dev);
#endif
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);r->close_stage=3U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
 ret=wr_iot_virtual_down_checked(ad,ticket);
 if(ret!=NDIS_STATUS_SUCCESS)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_ref_consume(r,dev,r->generation,r->last_token)){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;
 }
 r->close_stage=4U;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 RT_MOD_DEC_USE_COUNT();
 return 0;
uncertain:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);r->close_stage=5U;RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return -1;
}
