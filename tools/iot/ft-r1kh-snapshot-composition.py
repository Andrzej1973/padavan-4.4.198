"""Prepare an owned PMK-R1 cache snapshot API; no native caller is replaced.

Adapter/cache-lock lifetime remains the caller's responsibility. A snapshot
owns copied values only and cannot be passed to FT_R1khEntryDelete.
"""

PROTOTYPE = '''BOOLEAN wr_ft_r1kh_snapshot(RTMP_ADAPTER *pAd,
 const UCHAR *name, FT_R1HK_ENTRY *snapshot);'''

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
