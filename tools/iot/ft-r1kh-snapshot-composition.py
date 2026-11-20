"""Prepare an owned PMK-R1 cache snapshot API; no native caller is replaced.

Adapter/cache-lock lifetime remains the caller's responsibility. A snapshot
owns copied values only and cannot be passed to FT_R1khEntryDelete.
"""

PROTOTYPE = '''BOOLEAN wr_ft_r1kh_snapshot(RTMP_ADAPTER *pAd,
 const UCHAR *name, FT_R1HK_ENTRY *snapshot);
BOOLEAN wr_ft_r1kh_store(RTMP_ADAPTER *pAd,
 const FT_R1HK_ENTRY *value);'''

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
}'''


def compose(source, header):
    if 'wr_ft_r1kh_snapshot(' in source or 'wr_ft_r1kh_snapshot(' in header:
        raise ValueError('FT R1KH snapshot already prepared')
    anchor = 'PFT_R1HK_ENTRY FT_R1khEntryTabLookup('
    if source.count(anchor) != 1 or header.count(anchor) != 1:
        raise ValueError('FT R1KH snapshot requires exact native lookup anchors')
    start = source.index(anchor)
    end = source.index('\n}', start)+2
    return (source[:end]+'\n\n'+FUNCTION+'\n'+source[end:],
            header.replace(anchor, PROTOTYPE+'\n\n'+anchor, 1))
