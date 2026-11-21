"""Prepare an explicit-stamp native RX enqueue variant; never producer-installed.

Original receive enqueue and its callers remain byte-identical. The caller
captures the expected identity under MacTabLock and retains adapter/BSS lifetime.
This transfers identity only; receiver validation/lease is still mandatory.
"""
def one(text,old,new,count=1):
    if text.count(old)!=count:raise ValueError('FT enqueue anchor changed: '+old[:80])
    return text.replace(old,new)

def compose(text):
    name='wr_ft_mlme_enqueue_for_recv'
    if name in text:raise ValueError('FT explicit enqueue already prepared')
    start=text.index('BOOLEAN MlmeEnqueueForRecv(')
    end=text.index('\n}',start)+2
    original=text[start:end]
    body=one(original,'BOOLEAN MlmeEnqueueForRecv(', 'BOOLEAN '+name+'(')
    body=one(body,'IN UCHAR OpMode)',
      'IN UCHAR OpMode,\n IN const struct wr_ft_peer_stamp *wr_expected)')
    body=one(body,'\tif (!pFrame)', ''' if(!wr_expected||!wr_expected->generation||
  Wcid!=wr_expected->wcid||Wcid==RESERVED_WCID||Wcid>=MAX_LEN_OF_MAC_TABLE||
  MsgLen<LENGTH_802_11+offsetof(FT_ACTION,Oct))return FALSE;
\tif (!pFrame)''')
    capture='wr_stamp = wr_assoc_capture(pAd, Machine, MsgLen, Msg, Wcid);'
    transfer='''if(Machine!=ACTION_STATE_MACHINE||MsgType!=FT_CATEGORY_BSS_TRANSITION||
  MsgLen<LENGTH_802_11||wr_expected->bss>=pAd->ApCfg.BssidNum||
  wr_expected->bss>=sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0])||
  !MAC_ADDR_EQUAL(pFrame->Hdr.Addr2,wr_expected->addr)||
  !MAC_ADDR_EQUAL(pFrame->Hdr.Addr1,pAd->ApCfg.MBSSID[wr_expected->bss].wdev.bssid))return FALSE;
 wr_stamp.gen=wr_expected->generation;wr_stamp.wcid=wr_expected->wcid;
 COPY_MAC_ADDR(wr_stamp.addr,wr_expected->addr);'''
    body=one(body,capture,transfer,2)
    prototype=body[:body.index('{')].rstrip()+';'
    addition='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n'+prototype+'\n'+body+'\n#endif\n'
    return text[:end]+addition+text[end:],prototype

def bind_ft(text,prototype,pending_prototype=None,insert_prototype=None):
    """Prepare the existing-peer consumer plus pending-ticket first-peer path.

    Ordinary RX remains zero-stamp and is still an explicit integration gap.
    The pending path accepts a first-peer insert only with its queued BSS+MAC
    ticket; no native MAC-only insertion fallback remains in this candidate.
    """
    if 'wr_ft_expected' in text:raise ValueError('FT snapshot binding already prepared')
    include='#include "rt_config.h"'
    extra=''
    if pending_prototype is not None:extra+='\n'+pending_prototype
    if insert_prototype is not None:extra+='\n'+insert_prototype
    text=one(text,include,include+'\n#include "assoc-generation-kernel.h"\n'
        '#include "ft-peer-generation.h"\n#include "ft-pending-peer-scope.h"\n'
        '#include "ft-pending-queue.h"\n'+prototype+extra)
    start=text.index('VOID FT_RrbHandler(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'\tULONG Wcid;', '\tULONG Wcid;\n struct wr_ft_peer_stamp wr_ft_expected={0};\n'
      ' struct wr_ft_pending_token wr_ft_ticket={0};int wr_ft_has_pending=0;')
    producer_anchor=''' Wcid=RESERVED_WCID;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 for(slot=1;slot<MAX_LEN_OF_MAC_TABLE;slot++){
  pEntry=&pAd->MacTab.Content[slot];
  if(IS_ENTRY_CLIENT(pEntry)&&
     (pEntry->Sst==SST_AUTH||pEntry->Sst==SST_ASSOC)&&
     pEntry->wcid==slot&&pEntry->func_tb_idx==apidx&&
     pEntry->wdev==&pAd->ApCfg.MBSSID[apidx].wdev&&
     MAC_ADDR_EQUAL(pEntry->Addr,pSA)){
   Wcid=slot;break;
  }
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(Wcid==RESERVED_WCID)return;'''
    producer_replacement=''' Wcid=RESERVED_WCID;
 {
  int wr_seen_key=0;
  NdisAcquireSpinLock(&pAd->MacTabLock);
  for(slot=1;slot<MAX_LEN_OF_MAC_TABLE;slot++){
   pEntry=&pAd->MacTab.Content[slot];
   if(!IS_ENTRY_NONE(pEntry)&&MAC_ADDR_EQUAL(pEntry->Addr,pSA)&&
      (pEntry->func_tb_idx==apidx||
       pEntry->wdev==&pAd->ApCfg.MBSSID[apidx].wdev)){
    wr_seen_key=1;
    if(IS_ENTRY_CLIENT(pEntry)&&
       (pEntry->Sst==SST_AUTH||pEntry->Sst==SST_ASSOC)&&
       pEntry->wcid==slot&&pEntry->func_tb_idx==apidx&&
       pEntry->wdev==&pAd->ApCfg.MBSSID[apidx].wdev&&
       wr_ft_peer_capture_locked(pAd,slot,apidx,pSA,&wr_ft_expected))
     Wcid=slot;
    break;
   }
  }
  if(!wr_seen_key&&pFtAction->Action==FT_ACTION_BT_REQ&&
     MAC_ADDR_EQUAL(pFtAction->TargetApAddr,
       pAd->ApCfg.MBSSID[apidx].wdev.bssid)&&
     wr_ft_pending_reserve_locked(&pAd->wr_ft_pending,apidx,pSA,
       &wr_ft_ticket))wr_ft_has_pending=1;
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }
 if(Wcid==RESERVED_WCID&&!wr_ft_has_pending)return;'''
    body=one(body,producer_anchor,producer_replacement)
    body=one(body,'\t	DBGPRINT(RT_DEBUG_OFF, ("%s: allocate auth buffer fail!\\n",\n\t\t\t\t\t__FUNCTION__));\n\t\treturn;',
      '\t\tDBGPRINT(RT_DEBUG_OFF, ("%s: allocate auth buffer fail!\\n",\n\t\t\t\t\t__FUNCTION__));\n'
      '  if(wr_ft_ticket.generation){NdisAcquireSpinLock(&pAd->MacTabLock);\n'
      '   (void)wr_ft_pending_release_locked(&pAd->wr_ft_pending,&wr_ft_ticket);\n'
      '   NdisReleaseSpinLock(&pAd->MacTabLock);}\n\t\treturn;')
    report='REPORT_MGMT_FRAME_TO_MLME(pAd, Wcid, pOutBuffer, FrameLen, 0, 0, 0, 0, 0);'
    send='''{
 struct raw_rssi_info wr_rssi;
 NdisZeroMemory(&wr_rssi,sizeof(wr_rssi));
 if(wr_ft_has_pending){
  (void)wr_ft_pending_enqueue_for_recv(pAd,RESERVED_WCID,&wr_rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
   FrameLen,pOutBuffer,0,&wr_ft_ticket);
  if(wr_ft_ticket.generation){
   NdisAcquireSpinLock(&pAd->MacTabLock);
   (void)wr_ft_pending_release_locked(&pAd->wr_ft_pending,&wr_ft_ticket);
   NdisReleaseSpinLock(&pAd->MacTabLock);
  }
 }else{
  (void)wr_ft_mlme_enqueue_for_recv(pAd,Wcid,&wr_rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
   0,0,
#endif
   FrameLen,pOutBuffer,0,&wr_ft_expected);
 }
 }'''
    body=one(body,report,send)
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'\tPMAC_TABLE_ENTRY pEntry;',
      '\tPMAC_TABLE_ENTRY pEntry;\n struct wr_ft_peer_scope wr_ft_scope={0};\n'
      ' struct wr_ft_pending_peer_scope wr_ft_pending_scope={0};\n'
      ' struct wr_ft_pending_token wr_ft_ticket={0};int wr_ft_has_pending=0;')
    anchor='\tpFtCfg = &pAd->ApCfg.MBSSID[apidx].FtCfg;'
    admission=''' if(Elem->assoc_gen){
 struct wr_ft_peer_stamp wr_ft_expected={0};int wr_entered=0;
 if(Elem->Wcid!=Elem->assoc_wcid||
  !MAC_ADDR_EQUAL(pHdr->Addr2,Elem->assoc_addr))goto out;
 wr_ft_expected.generation=Elem->assoc_gen;
 wr_ft_expected.wcid=Elem->assoc_wcid;wr_ft_expected.bss=apidx;
 COPY_MAC_ADDR(wr_ft_expected.addr,Elem->assoc_addr);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 wr_entered=wr_ft_peer_enter_locked(pAd,&wr_ft_expected,&wr_ft_scope);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!wr_entered)goto out;
 }
'''
    body=one(body,anchor,admission+anchor)
    insert_anchor='''NdisReleaseSpinLock(&pAd->MacTabLock);
				if (!pEntry)
					pEntry = MacTableInsertEntry(pAd, pHdr->Addr2,
									&pAd->ApCfg.MBSSID[apidx].wdev, ENTRY_CLIENT, OPMODE_AP, TRUE);
 if(!pEntry)goto out;'''
    insert_gate='''NdisReleaseSpinLock(&pAd->MacTabLock);
 if(Elem->ft_pending_generation){
  if(Elem->assoc_gen||!wr_ft_pending_elem_snapshot(Elem,&wr_ft_ticket)||
   wr_ft_ticket.bss!=apidx||
   !MAC_ADDR_EQUAL(wr_ft_ticket.addr,pHdr->Addr2)||
   !MAC_ADDR_EQUAL(pFtAction->StaMac,wr_ft_ticket.addr))goto out;
  wr_ft_has_pending=1;
  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(!wr_ft_pending_current_locked(&pAd->wr_ft_pending,&wr_ft_ticket)){
   NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
  }
  if(pEntry){
   (void)wr_ft_pending_retire_key_locked(&pAd->wr_ft_pending,apidx,pHdr->Addr2);
   NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
  }
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }else if(!Elem->assoc_gen)goto out;
 if(!pEntry){
  if(!wr_ft_has_pending)goto out;
  pEntry=wr_ft_pending_insert(pAd,pHdr->Addr2,
   &pAd->ApCfg.MBSSID[apidx].wdev,&wr_ft_ticket,&wr_ft_pending_scope);
 }
 if(!pEntry)goto out;'''
    body=one(body,insert_anchor,insert_gate)
    body=one(body,'pEntry->Sst = SST_AUTH;', '''pEntry->Sst = SST_AUTH;
 if(wr_ft_pending_scope.active){
  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(!wr_ft_pending_peer_advance_locked(pAd,pEntry,&wr_ft_pending_scope)){
   NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
  }
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }else if(wr_ft_scope.active){
  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(!wr_ft_peer_advance_locked(pAd,pEntry,&wr_ft_scope)){
   NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
  }
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }else goto out;
''')
    body=one(body,'\nout:', '''
out:
 if(wr_ft_scope.active||wr_ft_pending_scope.active){
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(wr_ft_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);
 if(wr_ft_pending_scope.active)(void)wr_ft_pending_peer_leave_locked(pAd,&wr_ft_pending_scope);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 }
''')
    text=text[:start]+body+text[end:]
    return text
