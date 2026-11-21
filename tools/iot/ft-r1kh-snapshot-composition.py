"""Prepare PMK-R1 snapshot APIs and selected native caller conversions.

This composition is uninstalled; source conversion is not runtime validation.

Adapter/cache-lock lifetime remains the caller's responsibility. A snapshot
owns copied values only and cannot be passed to FT_R1khEntryDelete.
"""

PROTOTYPE = '''BOOLEAN wr_ft_r1kh_snapshot(RTMP_ADAPTER *pAd,
 const UCHAR *name, FT_R1HK_ENTRY *snapshot);
BOOLEAN wr_ft_r1kh_store(RTMP_ADAPTER *pAd,
 const FT_R1HK_ENTRY *value);
BOOLEAN wr_ft_r1kh_delete(RTMP_ADAPTER *pAd, const UCHAR *name);
INT wr_ft_r1kh_store_fields(RTMP_ADAPTER *, PUINT8, PUINT8, PUINT8,
 PUINT8, PUINT8, UINT32, UINT32, PUINT8, UINT8, PUINT8);
/* -1 failed, 0 same PMK-R1 key already present, 1 inserted/replaced. */
INT wr_ft_r1kh_response_store(RTMP_ADAPTER *, const FT_R1HK_ENTRY *);'''

FUNCTION = '''BOOLEAN wr_ft_r1kh_snapshot(RTMP_ADAPTER *pAd,
 const UCHAR *name, FT_R1HK_ENTRY *snapshot)
{
 PFT_R1HK_ENTRY entry;
 UINT8 hash;
 BOOLEAN found=FALSE;
 if(!snapshot)return FALSE;
 NdisZeroMemory(snapshot,sizeof(*snapshot));
 if(!pAd||!name)return FALSE;
 hash=FT_R1KH_HASH_INDEX(name);
 RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 if(pAd->ApCfg.FtTab.FT_R1khEntryTabReady){
  entry=(PFT_R1HK_ENTRY)pAd->ApCfg.FtTab.FT_R1khEntryTab[hash].pHead;
  while(entry){
   if(RTMPEqualMemory(name,entry->PmkR1Name,FT_KDP_WPA_NAME_MAX_SIZE)){
    if(entry->R0khIdLen<=sizeof(entry->R0khId)-1){
     NdisMoveMemory(snapshot,entry,sizeof(*snapshot));
     snapshot->pNext=NULL;
     found=TRUE;
    }
    break;
   }
   entry=entry->pNext;
  }
 }
 RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 return found;
}

/* Caller supplies owned values and separately holds request/adapter admission.
 * All cache consumers must use owned snapshots before this API is installed.
 * Allocation failure never removes the existing entry. */
BOOLEAN wr_ft_r1kh_store(RTMP_ADAPTER *pAd, const FT_R1HK_ENTRY *value)
{
 PFT_R1HK_ENTRY fresh=NULL,old=NULL,entry;
 LIST_HEADER *bucket;
 UINT8 hash;
 BOOLEAN stored=FALSE;
 if(!pAd||!value||value->R0khIdLen>sizeof(value->R0khId)-1)return FALSE;
 if(os_alloc_mem(pAd,(UCHAR **)&fresh,sizeof(*fresh))!=NDIS_STATUS_SUCCESS)
  return FALSE;
 NdisMoveMemory(fresh,value,sizeof(*fresh));
 fresh->pNext=NULL;
 hash=FT_R1KH_HASH_INDEX(fresh->PmkR1Name);
 RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 bucket=&pAd->ApCfg.FtTab.FT_R1khEntryTab[hash];
 if(pAd->ApCfg.FtTab.FT_R1khEntryTabReady){
  entry=(PFT_R1HK_ENTRY)bucket->pHead;
  while(entry){
   if(RTMPEqualMemory(fresh->PmkR1Name,entry->PmkR1Name,FT_KDP_WPA_NAME_MAX_SIZE)){
    old=entry;break;
   }
   entry=entry->pNext;
  }
  if(old||pAd->ApCfg.FtTab.FT_R1khEntryTabSize<FT_R1KH_ENTRY_TABLE_SIZE){
   if(old)delEntryList(bucket,(RT_LIST_ENTRY *)old);
   else pAd->ApCfg.FtTab.FT_R1khEntryTabSize++;
   insertTailList(bucket,(RT_LIST_ENTRY *)fresh);
   stored=TRUE;
  }
 }
 RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 if(old)os_free_mem(pAd,old);
 if(!stored)os_free_mem(pAd,fresh);
 return stored;
}

/* Delete by immutable key; callers never pass an entry pointer across unlock. */
BOOLEAN wr_ft_r1kh_delete(RTMP_ADAPTER *pAd, const UCHAR *name)
{
 PFT_R1HK_ENTRY entry,retired=NULL;
 LIST_HEADER *bucket;
 UINT8 hash;
 if(!pAd||!name)return FALSE;
 hash=FT_R1KH_HASH_INDEX(name);
 RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 bucket=&pAd->ApCfg.FtTab.FT_R1khEntryTab[hash];
 if(pAd->ApCfg.FtTab.FT_R1khEntryTabReady){
  entry=(PFT_R1HK_ENTRY)bucket->pHead;
  while(entry){
   if(RTMPEqualMemory(name,entry->PmkR1Name,FT_KDP_WPA_NAME_MAX_SIZE)){
    delEntryList(bucket,(RT_LIST_ENTRY *)entry);
    if(pAd->ApCfg.FtTab.FT_R1khEntryTabSize)
     pAd->ApCfg.FtTab.FT_R1khEntryTabSize--;
    retired=entry;
    break;
   }
   entry=entry->pNext;
  }
 }
 RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 if(retired)os_free_mem(pAd,retired);
 return retired!=NULL;
}

/* Build a fully owned value and atomically replace/insert it. */
INT wr_ft_r1kh_store_fields(RTMP_ADAPTER *pAd, PUINT8 pPmkR0Name,
 PUINT8 pPmkR1Name, PUINT8 pPmkR1Key, PUINT8 pPairwisChipher,
 PUINT8 pAkmSuite, UINT32 KeyLifeTime, UINT32 RassocDeadline,
 PUINT8 pR0khId, UINT8 R0khIdLen, PUINT8 pStaMac)
{
 FT_R1HK_ENTRY value;
 if(!pPmkR1Name||R0khIdLen>sizeof(value.R0khId)-1||
    (R0khIdLen&&!pR0khId))return -1;
 NdisZeroMemory(&value,sizeof(value));
 if(pStaMac)NdisMoveMemory(value.StaMac,pStaMac,MAC_ADDR_LEN);
 if(pR0khId&&R0khIdLen){value.R0khIdLen=R0khIdLen;NdisMoveMemory(value.R0khId,pR0khId,R0khIdLen);}
 if(pPairwisChipher)NdisMoveMemory(value.PairwisChipher,pPairwisChipher,4);
 if(pAkmSuite)NdisMoveMemory(value.AkmSuite,pAkmSuite,4);
 if(pPmkR0Name)NdisMoveMemory(value.PmkR0Name,pPmkR0Name,16);
 NdisMoveMemory(value.PmkR1Name,pPmkR1Name,16);
 if(pPmkR1Key)NdisMoveMemory(value.PmkR1Key,pPmkR1Key,32);
 value.KeyLifeTime=KeyLifeTime;value.RassocDeadline=RassocDeadline;
 return wr_ft_r1kh_store(pAd,&value)?0:-1;
}

/* Compare and replace by PMKR1Name in one cache-lock transaction. No raw
 * entry pointer escapes, and a same-key response is distinguishable from a
 * failed store so its caller can complete the exact matching AUTH waiter. */
INT wr_ft_r1kh_response_store(RTMP_ADAPTER *pAd, const FT_R1HK_ENTRY *value)
{
 PFT_R1HK_ENTRY fresh=NULL,old=NULL,entry;
 LIST_HEADER *bucket;
 UINT8 hash;
 INT result=-1;
 if(!pAd||!value||value->R0khIdLen>sizeof(value->R0khId)-1)return -1;
 if(os_alloc_mem(pAd,(UCHAR **)&fresh,sizeof(*fresh))!=NDIS_STATUS_SUCCESS)
  return -1;
 NdisMoveMemory(fresh,value,sizeof(*fresh));
 fresh->pNext=NULL;
 hash=FT_R1KH_HASH_INDEX(fresh->PmkR1Name);
 RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 bucket=&pAd->ApCfg.FtTab.FT_R1khEntryTab[hash];
 if(pAd->ApCfg.FtTab.FT_R1khEntryTabReady){
  entry=(PFT_R1HK_ENTRY)bucket->pHead;
  while(entry){
   if(RTMPEqualMemory(fresh->PmkR1Name,entry->PmkR1Name,FT_KDP_WPA_NAME_MAX_SIZE)){
    old=entry;break;
   }
   entry=entry->pNext;
  }
  if(old&&RTMPEqualMemory(old->PmkR1Key,fresh->PmkR1Key,LEN_PMK))
   result=0;
  else if(old||pAd->ApCfg.FtTab.FT_R1khEntryTabSize<FT_R1KH_ENTRY_TABLE_SIZE){
   if(old)delEntryList(bucket,(RT_LIST_ENTRY *)old);
   else pAd->ApCfg.FtTab.FT_R1khEntryTabSize++;
   insertTailList(bucket,(RT_LIST_ENTRY *)fresh);
   result=1;
  }
 }
 RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
 if(old&&result==1)os_free_mem(pAd,old);
 if(result!=1)os_free_mem(pAd,fresh);
 return result;
}'''


def compose(source, header):
    if 'wr_ft_r1kh_snapshot(' in source or 'wr_ft_r1kh_snapshot(' in header:
        raise ValueError('FT R1KH snapshot already prepared')
    anchor = 'PFT_R1HK_ENTRY FT_R1khEntryTabLookup('
    if source.count(anchor) != 1 or header.count(anchor) != 1:
        raise ValueError('FT R1KH snapshot requires exact native lookup anchors')
    start = source.index(anchor)
    end = source.index('\n}', start)+2
    prepared_source=source[:end]+'\n\n'+FUNCTION+'\n'+source[end:]
    prepared_source=_convert_ft_readers(prepared_source)
    prepared_source=_convert_query_reader(prepared_source)
    prepared_source=_convert_native_insert(prepared_source)
    prepared_source=_convert_auth_writer(prepared_source)
    return (prepared_source, header.replace(anchor, PROTOTYPE+'\n\n'+anchor, 1))


def compose_related(sources):
    """Convert the non-ft.c readers while preserving their surrounding source."""
    result=dict(sources)
    cmm=result['common/cmm_wpa.c']
    local='PFT_R1HK_ENTRY pR1khEntry;'
    if cmm.count(local)!=1:
        raise ValueError('cmm_wpa FT cache local changed')
    cmm=cmm.replace(local,'FT_R1HK_ENTRY r1khSnapshot;\n\t\t\t\tPFT_R1HK_ENTRY pR1khEntry = &r1khSnapshot;',1)
    import re
    old=(r'/\* Delete previous entry \*/\s*'
      r'pR1khEntry = FT_R1khEntryTabLookup\(pAd, pEntry->FT_PMK_R1_NAME\);\s*'
      r'if \(pR1khEntry != NULL\)\s*\{\s*'
      r'FT_R1khEntryDelete\(pAd, pR1khEntry\);\s*\}')
    cmm,n=re.subn(old,'/* Atomic insert replaces the prior value. */',cmm)
    if n!=1:raise ValueError('cmm_wpa delete-before-insert block changed')
    lookup='pR1khEntry = FT_R1khEntryTabLookup(pAd, pEntry->FT_PMK_R1_NAME);'
    if cmm.count(lookup)!=1:raise ValueError('cmm_wpa diagnostic lookup changed')
    cmm=cmm.replace(lookup,'pR1khEntry = wr_ft_r1kh_snapshot(pAd, pEntry->FT_PMK_R1_NAME, pR1khEntry) ? pR1khEntry : NULL;')
    result['common/cmm_wpa.c']=cmm

    ap=result['ap/ap_ftkd.c']
    signature='VOID TYPE_FUNC FT_KDP_KeyResponseToUs('
    if ap.count(signature)!=1:raise ValueError('FT KDP response handler changed')
    start=ap.index(signature);end=ap.index('\n}',start)+2;body=ap[start:end]
    declaration='FT_KDP_EVT_KEY_ELM *pEvtKeyRsp;'
    if body.count(declaration)!=1:raise ValueError('FT KDP response declaration changed')
    body=body.replace(declaration,declaration+'\n\tFT_KDP_EVT_KEY_ELM wr_owned_response;',1)
    parse='IAPP_DAEMON_CMD_PARSE(pInfo, InfoLen, PeerIP, pData, DataLen);'
    if body.count(parse)!=1:raise ValueError('FT KDP response parse anchor changed')
    body=body.replace(parse,
      'if (!pInfo || InfoLen < 0 || (UINT32)InfoLen < '+
      'FT_IP_ADDRESS_SIZE + FT_NONCE_SIZE + sizeof(wr_owned_response)) return;\n\t'+parse,1)
    borrow='pEvtKeyRsp = (FT_KDP_EVT_KEY_ELM *)(pNonce + FT_NONCE_SIZE);'
    if body.count(borrow)!=1:raise ValueError('FT KDP response payload anchor changed')
    body=body.replace(borrow,
      'NdisMoveMemory(&wr_owned_response, pNonce + FT_NONCE_SIZE, sizeof(wr_owned_response));\n'
      '\tpEvtKeyRsp = &wr_owned_response;\n'
      '\tif (pEvtKeyRsp->KeyInfo.R0KHIDLen > sizeof(pEvtKeyRsp->KeyInfo.R0KHID)) return;',1)
    format_check='(pEvtKeyRsp->ElmId == FT_KDP_ELM_ID_PRI) &&'
    if body.count(format_check)!=1:raise ValueError('FT KDP response format anchor changed')
    body=body.replace(format_check,format_check+'\n\t\t(pEvtKeyRsp->ElmLen == FT_KDP_ELM_PRI_LEN) &&',1)

    body,n=re.subn(r'PFT_R1HK_ENTRY\s+pR1hkEntry;',
      'FT_R1HK_ENTRY r1khSnapshot;\\n\\t\\tPFT_R1HK_ENTRY pR1hkEntry = &r1khSnapshot;',body,count=1)
    if n!=1:raise ValueError('FT KDP response cache local changed')
    lookup='pR1hkEntry = FT_R1khEntryTabLookup(pAd, pEvtKeyRsp->PMKR1Name);'
    if body.count(lookup)!=1:raise ValueError('FT KDP response lookup changed')
    body=body.replace(lookup,'pR1hkEntry = wr_ft_r1kh_snapshot(pAd, pEvtKeyRsp->PMKR1Name, pR1hkEntry) ? pR1hkEntry : NULL;')
    delete='FT_R1khEntryDelete(pAd, pR1hkEntry);'
    if body.count(delete)!=1:raise ValueError('FT KDP response delete changed')
    body=body.replace(delete,'/* Atomic store replaces the previous value. */')
    # Do not reset retry state or complete the waiter when cache storage fails.
    store='FT_R1khEntryInsert(pAd,'
    if body.count(store)!=1:
        raise ValueError('FT KDP response store changed')
    call_start=body.index(store)
    call_end=body.index(';',call_start)+1
    call=body[call_start:call_end-1]
    body=body[:call_start]+'if ('+call+' < 0) return;'+body[call_end:]
    result['ap/ap_ftkd.c']=ap[:start]+body+ap[end:]
    return result


def _convert_ft_readers(source):
    specs=(
      ('UINT16\tFT_AuthConfirmRsnValidation(',1,'return FT_STATUS_CODE_RESERVED;'),
      ('UINT16\tFT_AssocReqRsnValidation(',1,'return FT_STATUS_CODE_RESERVED;'))
    for name,count,failure in specs:
        start=source.index(name,source.index(name)+1)
        end=source.index('\n}',start)+2
        body=source[start:end]
        if 'PFT_R1HK_ENTRY pR1hkEntry = NULL;' not in body:
            raise ValueError('missing raw entry local in '+name)
        body=body.replace('PFT_R1HK_ENTRY pR1hkEntry = NULL;',
          'FT_R1HK_ENTRY r1khSnapshot;\n\tPFT_R1HK_ENTRY pR1hkEntry = &r1khSnapshot;')
        lookup='pR1hkEntry = FT_R1khEntryTabLookup(pAd, pEntry->FT_PMK_R1_NAME);'
        if body.count(lookup)!=count:
            raise ValueError('unexpected lookup count in '+name)
        body=body.replace(lookup,'if (!wr_ft_r1kh_snapshot(pAd, pEntry->FT_PMK_R1_NAME, pR1hkEntry)) '+failure)
        source=source[:start]+body+source[end:]
    return source


def _convert_query_reader(source):
    signature='BOOLEAN FT_QueryKeyInfoForKDP('
    if source.count(signature)!=1:
        raise ValueError('expected one PMK-R1 query reader')
    start=source.index(signature);end=source.index('\n}',start)+2;body=source[start:end]
    if 'PFT_R1HK_ENTRY pR1khEntry;' not in body:
        raise ValueError('PMK-R1 query reader local changed')
    body=body.replace('PFT_R1HK_ENTRY pR1khEntry;',
      'FT_R1HK_ENTRY r1khSnapshot;\n\tPFT_R1HK_ENTRY pR1khEntry = &r1khSnapshot;')
    lookup='pR1khEntry = FT_R1khEntryTabLookup(pAd, OriPMKR1Name);'
    if body.count(lookup)!=1:raise ValueError('PMK-R1 query lookup changed')
    body=body.replace(lookup,'if (!wr_ft_r1kh_snapshot(pAd, OriPMKR1Name, pR1khEntry)) return FALSE;')
    return source[:start]+body+source[end:]


def _convert_native_insert(source):
    signature='INT FT_R1khEntryInsert('
    if source.count(signature)!=1:
        raise ValueError('native insert definition changed')
    start=source.index(signature)
    brace=source.index('{',start)
    end=source.index('\n}',brace)+2
    declaration=source[start:brace]
    body='''{
 return wr_ft_r1kh_store_fields(pAd,pPmkR0Name,pPmkR1Name,pPmkR1Key,
  pPairwisChipher,pAkmSuite,KeyLifeTime,RassocDeadline,pR0khId,R0khIdLen,pStaMac);
}'''
    return source[:start]+declaration+body+source[end:]


def _convert_auth_writer(source):
    signature='UINT16\tFT_AuthReqRsnValidation('
    start=source.index(signature,source.index(signature)+1)
    end=source.index('\n}',start)+2
    body=source[start:end]
    if body.count('PFT_R1HK_ENTRY pR1hkEntry = NULL;')!=1:
        raise ValueError('AUTH cache snapshot local changed')
    body=body.replace('PFT_R1HK_ENTRY pR1hkEntry = NULL;',
      'FT_R1HK_ENTRY r1khSnapshot;\n\tPFT_R1HK_ENTRY pR1hkEntry = &r1khSnapshot;')
    import re
    pattern=(r'\s*/\* Delete previous entry \*/\s*'
      r'pR1hkEntry = FT_R1khEntryTabLookup\(pAd, pEntry->FT_PMK_R1_NAME\);\s*'
      r'if \(pR1hkEntry != NULL\)\s*\{\s*'
      r'FT_R1khEntryDelete\(pAd, pR1hkEntry\);\s*\}\s*'
      r'/\* Update R1KH table \*/')
    body,count=re.subn(pattern,'\n\t\t/* Store performs atomic same-name replacement. */\n\t\t/* Update R1KH table */',body)
    if count!=1:
        raise ValueError('AUTH delete-before-insert block changed')
    lookup='pR1hkEntry = FT_R1khEntryTabLookup(pAd, pEntry->FT_PMK_R1_NAME);'
    if body.count(lookup)!=2:
        raise ValueError('AUTH post-store/cache lookup count changed')
    body=body.replace(lookup,'pR1hkEntry = wr_ft_r1kh_snapshot(pAd, pEntry->FT_PMK_R1_NAME, &r1khSnapshot) ? &r1khSnapshot : NULL;')
    body=body.replace('hex_dump("Own PMKR0Name", pR1hkEntry->PmkR0Name, LEN_PMK_NAME);',
      'hex_dump("Own PMKR0Name", r1khSnapshot.PmkR0Name, LEN_PMK_NAME);')
    insert='FT_R1khEntryInsert(pAd,'
    if body.count(insert)!=1:
        raise ValueError('AUTH cache store call changed')
    body=body.replace(insert,'if (FT_R1khEntryInsert(pAd,',1)
    final_arg='pEntry->Addr);'
    if body.count(final_arg)!=1:
        raise ValueError('AUTH cache store final argument changed')
    body=body.replace(final_arg,'pEntry->Addr) < 0) return MLME_FAIL_NO_RESOURCE;',1)
    return source[:start]+body+source[end:]
