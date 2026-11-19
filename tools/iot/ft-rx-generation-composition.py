"""Bind ordinary received FT action frames to exact active BSS peers or tickets."""


def one(text, old, new):
    if text.count(old) != 1:
        raise ValueError('ordinary FT RX anchor changed: ' + old[:90])
    return text.replace(old, new, 1)


def compose(text, active_prototype, pending_prototype):
    if 'wr_ft_rx_pending' in text or 'wr_ft_native_mlme_enqueue_for_recv' in text:
        raise ValueError('ordinary FT RX binder already prepared')
    start = text.index('BOOLEAN MlmeEnqueueForRecv(')
    end = text.index('\n}', start) + 2
    native = text[start:end]
    renamed = one(native, 'BOOLEAN MlmeEnqueueForRecv(',
                  'static BOOLEAN wr_ft_native_mlme_enqueue_for_recv(')
    prototype = native[:native.index('{')].rstrip()
    wrapper = prototype + '''
{
#ifdef DOT11R_FT_SUPPORT
 PFRAME_802_11 wr_frame=(PFRAME_802_11)Msg;
 if(pAd->OpMode==OPMODE_AP&&wr_frame&&MsgLen>=LENGTH_802_11+1&&
    wr_frame->Hdr.FC.Type==FC_TYPE_MGMT&&
    (wr_frame->Hdr.FC.SubType==SUBTYPE_ACTION||
     wr_frame->Hdr.FC.SubType==SUBTYPE_ACTION_NO_ACK)&&
    *((const UCHAR *)Msg+LENGTH_802_11)==FT_CATEGORY_BSS_TRANSITION){
  UCHAR wr_apidx;int wr_have_bss=0,wr_seen=0,wr_active=0;
  ULONG wr_wcid=RESERVED_WCID;struct wr_ft_peer_stamp wr_stamp={0};
  struct wr_ft_pending_token wr_ft_rx_pending={0};
  PFT_ACTION wr_action;
  if(MsgLen<LENGTH_802_11+offsetof(FT_ACTION,Oct))return FALSE;
  wr_action=(const PFT_ACTION)((const UCHAR *)Msg+LENGTH_802_11);
  if(!MAC_ADDR_EQUAL(wr_action->StaMac,wr_frame->Hdr.Addr2))return FALSE;
  for(wr_apidx=0;wr_apidx<pAd->ApCfg.BssidNum&&
      wr_apidx<sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);wr_apidx++)
   if(MAC_ADDR_EQUAL(wr_frame->Hdr.Addr1,
       pAd->ApCfg.MBSSID[wr_apidx].wdev.bssid)){wr_have_bss=1;break;}
  if(!wr_have_bss)return FALSE;
  NdisAcquireSpinLock(&pAd->MacTabLock);
  for(wr_wcid=1;wr_wcid<MAX_LEN_OF_MAC_TABLE;wr_wcid++){
   PMAC_TABLE_ENTRY wr_entry=&pAd->MacTab.Content[wr_wcid];
   if(!IS_ENTRY_NONE(wr_entry)&&MAC_ADDR_EQUAL(wr_entry->Addr,wr_frame->Hdr.Addr2)&&
      (wr_entry->func_tb_idx==wr_apidx||
       wr_entry->wdev==&pAd->ApCfg.MBSSID[wr_apidx].wdev)){
    if(wr_seen){wr_active=0;break;}
    wr_seen=1;
    if(IS_ENTRY_CLIENT(wr_entry)&&
       (wr_entry->Sst==SST_AUTH||wr_entry->Sst==SST_ASSOC)&&
       wr_entry->wcid==wr_wcid&&wr_entry->func_tb_idx==wr_apidx&&
       wr_entry->wdev==&pAd->ApCfg.MBSSID[wr_apidx].wdev&&
       wr_ft_peer_capture_locked(pAd,wr_wcid,wr_apidx,wr_frame->Hdr.Addr2,&wr_stamp))
     wr_active=1;
   }
  }
  if(!wr_seen&&wr_action->Action==FT_ACTION_BT_REQ&&
     MAC_ADDR_EQUAL(wr_action->TargetApAddr,wr_frame->Hdr.Addr1))
   (void)wr_ft_pending_reserve_locked(&pAd->wr_ft_pending,wr_apidx,
       wr_frame->Hdr.Addr2,&wr_ft_rx_pending);
  NdisReleaseSpinLock(&pAd->MacTabLock);
  if(wr_active)
   return wr_ft_mlme_enqueue_for_recv(pAd,wr_stamp.wcid,rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
    Snr0,Snr1,
#endif
    MsgLen,Msg,OpMode,&wr_stamp);
  if(wr_ft_rx_pending.generation){
   BOOLEAN wr_queued=wr_ft_pending_enqueue_for_recv(pAd,RESERVED_WCID,rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
    Snr0,Snr1,
#endif
    MsgLen,Msg,OpMode,&wr_ft_rx_pending);
   if(wr_ft_rx_pending.generation){
    NdisAcquireSpinLock(&pAd->MacTabLock);
    (void)wr_ft_pending_release_locked(&pAd->wr_ft_pending,&wr_ft_rx_pending);
    NdisReleaseSpinLock(&pAd->MacTabLock);
   }
   return wr_queued;
  }
  return FALSE;
 }
#endif
 return wr_ft_native_mlme_enqueue_for_recv(pAd,Wcid,rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  Snr0,Snr1,
#endif
  MsgLen,Msg,OpMode);
}
'''
    includes = ('\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n'
                '#include "ft-pending-queue.h"\n' + active_prototype + '\n'
                + pending_prototype + '\n#endif\n')
    return text[:start] + renamed + includes + wrapper + text[end:]
