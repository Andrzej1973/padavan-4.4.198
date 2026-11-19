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

def bind_ft(text,prototype):
    """Prepare the RRB producer and stamped existing-peer consumer only.

    Zero-stamp ordinary RX is deliberately still native: its initial-peer
    semantics must be covered before any producer installation is allowed.
    """
    if 'wr_ft_expected' in text:raise ValueError('FT snapshot binding already prepared')
    include='#include "rt_config.h"'
    text=one(text,include,include+'\n#include "ft-peer-generation.h"\n'+prototype)
    start=text.index('VOID FT_RrbHandler(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'\tULONG Wcid;', '\tULONG Wcid;\n struct wr_ft_peer_stamp wr_ft_expected={0};')
    body=one(body,'Wcid=slot;break;',
      'if(wr_ft_peer_capture_locked(pAd,slot,apidx,pSA,&wr_ft_expected)){Wcid=slot;break;}')
    report='REPORT_MGMT_FRAME_TO_MLME(pAd, Wcid, pOutBuffer, FrameLen, 0, 0, 0, 0, 0);'
    send='''{
 struct raw_rssi_info wr_rssi;
 NdisZeroMemory(&wr_rssi,sizeof(wr_rssi));
 (void)wr_ft_mlme_enqueue_for_recv(pAd,Wcid,&wr_rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  FrameLen,pOutBuffer,0,&wr_ft_expected);
 }'''
    body=one(body,report,send)
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'\tPMAC_TABLE_ENTRY pEntry;',
      '\tPMAC_TABLE_ENTRY pEntry;\n struct wr_ft_peer_scope wr_ft_scope={0};')
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
    body=one(body,'\nout:', '''
out:
 if(wr_ft_scope.active){
 NdisAcquireSpinLock(&pAd->MacTabLock);
 (void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 }
''')
    text=text[:start]+body+text[end:]
    return text
