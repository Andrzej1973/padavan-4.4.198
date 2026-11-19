"""Prepare bounded native FT action parsing; not producer-installed yet."""
def one(text,old,new,count=1):
    if text.count(old)!=count:raise ValueError('FT bounds anchor changed: '+old[:80])
    return text.replace(old,new)

def compose(source):
    if 'wr_iot_ft_request_ies_admitted' in source:raise ValueError('FT parser bounds already installed')
    text=one(source,'#include "rt_config.h"',
      '#include "rt_config.h"\n#include "ft-request-ie-admission.h"\n#include "ft-action-bounds.h"')
    start=text.index('static VOID FT_ReqActionParse(',text.index('static VOID FT_ReqActionParse(')+1)
    end=text.index('\n}',start)+2;body=text[start:end]
    body=one(body,'\tPEID_STRUCT eid_ptr;', '\tPEID_STRUCT eid_ptr;\n unsigned int remaining=Len;')
    anchor='\tNdisZeroMemory(pFtInfo, sizeof(FT_INFO));'
    body=one(body,anchor,anchor+'\n if(!wr_iot_ft_request_ies_admitted(Ptr,Len))return;')
    body=one(body,'while(((UCHAR*)eid_ptr + eid_ptr->Len + 1) < ((PUCHAR)Ptr + Len))',
      'while(remaining>=2)')
    advance='eid_ptr = (PEID_STRUCT)((UCHAR*)eid_ptr + 2 + eid_ptr->Len);'
    body=one(body,advance,'remaining -= 2 + eid_ptr->Len;\n        '+advance)
    # RIC view is exactly remaining bytes, not one byte beyond the input.
    body=one(body,'- (UCHAR*)eid_ptr + 1;', '- (UCHAR*)eid_ptr;')
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2;body=text[start:end]
    body=one(body,'\tUINT16 FtActLen;', '\tUINT16 FtActLen,wr_ie_length;')
    anchor='\tos_alloc_mem(pAd, (UCHAR **)&pFtInfo, sizeof(FT_INFO));'
    body=one(body,anchor,''' if(!Elem||!wr_iot_ft_action_payload_length(Elem->MsgLen,sizeof(Elem->Msg),
  LENGTH_802_11,offsetof(FT_ACTION,Oct),&wr_ie_length))return;
'''+anchor)
    check='if(!wr_iot_ft_request_ies_admitted(pFtAction->Oct,wr_ie_length))goto out;\n'
    body=one(body,'pEntry = MacTableLookup(pAd, pHdr->Addr2);',
      check+'\t\t\t\tpEntry = MacTableLookup(pAd, pHdr->Addr2);')
    body=one(body,'if (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)',
      check+'\t\t\t\tif (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)')
    allocation='&pAd->ApCfg.MBSSID[apidx].wdev, ENTRY_CLIENT, OPMODE_AP, TRUE);'
    body=one(body,allocation,allocation+'\n if(!pEntry)goto out;')
    body=one(body,'if (pEntry->func_tb_idx > pAd->ApCfg.BssidNum)',
      'if (pEntry->func_tb_idx >= pAd->ApCfg.BssidNum)')
    body=one(body,'(FtActLen - sizeof(PFT_ACTION))','wr_ie_length',2)
    # FtActLen remains needed for native forwarding of the complete action.
    text=text[:start]+body+text[end:]
    # Bind the RRB producer to an active client on its destination BSS.
    # Keep only the selected WCID after releasing MacTabLock. This snapshot
    # does not establish the queued association generation or pin a peer.
    start=text.index('VOID FT_RrbHandler(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'PFT_RRB pRrb = (PFT_RRB)(pPktSrc + LENGTH_802_3);','PFT_RRB pRrb;')
    body=one(body,'\tULONG Wcid;', '\tULONG Wcid;\n INT apidx;\n unsigned int slot;')
    anchor='\tStatus = MlmeAllocateMemory(pAd, &pOutBuffer);'
    admission=""" if(!pAd||!pPktSrc||PktLen<0||
  (ULONG)PktLen<LENGTH_802_3+offsetof(FT_RRB,Oct)+offsetof(FT_ACTION,Oct))return;
 pRrb=(PFT_RRB)(pPktSrc+LENGTH_802_3);
 if(pRrb->FTActLen<offsetof(FT_ACTION,Oct)||
  pRrb->FTActLen>(ULONG)PktLen-LENGTH_802_3-offsetof(FT_RRB,Oct)||
  sizeof(HEADER_802_11)>MGMT_DMA_BUFFER_SIZE||
  pRrb->FTActLen>MGMT_DMA_BUFFER_SIZE-sizeof(HEADER_802_11))return;
 apidx=get_apidx_by_addr(pAd,pPktSrc);
 if(apidx<0||apidx>=pAd->ApCfg.BssidNum)return;
 pFtAction=(PFT_ACTION)pRrb->Oct;
 pSA=pFtAction->StaMac;
 Wcid=RESERVED_WCID;
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
 if(Wcid==RESERVED_WCID)return;
"""
    body=one(body,anchor,admission+anchor)
    old='\tpEntry = MacTableLookup(pAd, pSA);\n\tif (pEntry)\n\t\tWcid = pEntry->wcid;\n\telse\n\t\tWcid = RESERVED_WCID;'
    body=one(body,old,'/* WCID selected under MacTabLock before allocation. */')
    text=text[:start]+body+text[end:]
    return text
