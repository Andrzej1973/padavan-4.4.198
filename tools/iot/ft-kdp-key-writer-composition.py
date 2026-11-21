"""Prepare checked key writer; native hash retained, publication locked.

Caller supplies a NUL-terminated owned input as required by native hash API.
"""
def compose(source,caller,header):
    signature='VOID TYPE_FUNC FT_KDP_CryptKeySet('
    if source.count(signature)!=1:raise ValueError('native key writer changed')
    if 'wr_ft_kdp_key_set_checked(' in source:raise ValueError('key writer already composed')
    start=source.index(signature);end=source.index('\n}',start)+2
    native=source[start:end].replace(signature,'static BOOLEAN wr_native_kdp_key_set(',1)
    native=native.replace('return;','return FALSE;')
    native=native.replace('{\n#ifndef FT_KDP_EMPTY','{\n (void)pAd;(void)pKey;(void)KeyLen;\n#ifndef FT_KDP_EMPTY',1)
    import re
    pattern=r'RtmpPasswordHash\([^;]+\);'
    calls=list(re.finditer(pattern,native))
    if len(calls)!=2:raise ValueError('native key hash calls changed')
    native=re.sub(pattern,lambda m:'if(!'+m[0][:-1]+'){'
        'unsigned int i;for(i=0;i<sizeof(KeyMaterial);i++)'
        '((volatile UCHAR *)KeyMaterial)[i]=0;return FALSE;}',native)
    anchor='NdisMoveMemory(FT_KDP_CB->CryptKey, KeyMaterial, sizeof(KeyMaterial));'
    if native.count(anchor)!=1:raise ValueError('key publication changed')
    native=native.replace(anchor,'RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_KdpLock);\n '+anchor+
      '\n RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_KdpLock);\n'
      ' {unsigned int i;for(i=0;i<sizeof(KeyMaterial);i++)((volatile UCHAR *)KeyMaterial)[i]=0;}\n return TRUE;',1)
    native=native.replace('#endif /* FT_KDP_EMPTY */','#endif /* FT_KDP_EMPTY */\n return FALSE;',1)
    wrapper='''
BOOLEAN wr_ft_kdp_key_set_checked(RTMP_ADAPTER *pAd,UCHAR *key,INT32 length)
{
 struct wr_ft_cache_lease lease={0};BOOLEAN ok;unsigned int i;
 if(!pAd||!key||length<0||!pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 /* The ioctl caller owns length+1 bytes and appends the terminator. Native
  * fallback for lengths outside8..64 does not consume caller key bytes. */
 if(length>=8&&length<=64){
  for(i=0;i<(unsigned int)length;i++)if(!key[i])return FALSE;
  if(key[length])return FALSE;
 }

 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_enter(&pAd->wr_ft_cache_lifetime,&lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!ok)return FALSE;
 ok=FALSE;
 if(pAd->ApCfg.FtTab.FlgIsFtKdpInit==1&&pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK)
  ok=wr_native_kdp_key_set(pAd,key,length);
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!wr_ft_cache_leave(&pAd->wr_ft_cache_lifetime,&lease))ok=FALSE;
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return ok;
}
'''
    call='FT_KDP_CryptKeySet(pAd, pBuffer, wrq->u.data.length);'
    if caller.count(call)!=1:raise ValueError('native key writer caller changed')
    caller=caller.replace(call,'if(!wr_ft_kdp_key_set_checked(pAd,pBuffer,wrq->u.data.length))Status=-EAGAIN;',1)
    # The outer grouped ioctl owns this buffer through copy and dispatch.
    # Clear only KEY_SET, preserving other grouped operation behavior.
    outer=caller.index('case RT_SET_FT_STATION_NOTIFY:')
    caller_end=caller.index('case OID_802_11R_SUPPORT:',outer)
    fragment=caller[outer:caller_end]
    release='FT_MEM_FREE(pAd, pBuffer);'
    if fragment.count(release)!=2:raise ValueError('key ioctl cleanup shape changed')
    wipe='''if((cmd & 0x7FFF)==RT_FT_KEY_SET){
 unsigned int wr_key_i;
 for(wr_key_i=0;wr_key_i<(unsigned int)wrq->u.data.length+1U;wr_key_i++)
  ((volatile UCHAR *)pBuffer)[wr_key_i]=0;
 }
 '''
    fragment=fragment.replace(release,wipe+release)
    caller=caller[:outer]+fragment+caller[caller_end:]
    proto='VOID FT_KDP_CryptKeySet('
    if header.count(proto)!=1:raise ValueError('key writer prototype changed')
    hstart=header.index(proto);hend=header.index(';',hstart)+1
    header=header[:hstart]+'BOOLEAN wr_ft_kdp_key_set_checked(RTMP_ADAPTER *,UCHAR *,INT32);'+header[hend:]
    return source[:start]+native+wrapper+source[end:],caller,header
