"""Prepare checked native cache lifecycle entry points, without installing them.

Callers must serialize AP lifecycle and propagate FALSE before any KDP/RIC/AP
teardown. Existing FT_Init/Release are deliberately not redirected here.
"""

def compose(source):
    if 'wr_ft_cache_initialize_checked(' in source:
        raise ValueError('native cache lifecycle already composed')
    bodies=[]
    for name in ('FT_R1khEntryTabInit','FT_R1khEntryTabDestroy'):
        signature='VOID '+name+'('
        if source.count(signature)!=1:
            raise ValueError('native cache lifecycle definition changed: '+name)
        start=source.index(signature);end=source.index('\n}',start)+2
        bodies.append(source[start:end].replace(signature,'static VOID wr_native_'+name+'(',1))
    anchor='NdisAllocateSpinLock(pAd, &(pAd->ApCfg.FtTab.FT_R1khEntryTabLock));'
    if bodies[0].count(anchor)!=1:
        raise ValueError('native cache lock allocation changed')
    # Native void init ignored OS_ABL allocation failure and still published Ready.
    # Checked clone leaves Ready false on allocation failure; publish then poisons.
    bodies[0]=bodies[0].replace(anchor,'''pAd->ApCfg.FtTab.FT_R1khEntryTabReady=FALSE;
#ifdef OS_ABL_FUNC_SUPPORT
 if(!NdisAllocateSpinLock(pAd,&pAd->ApCfg.FtTab.FT_R1khEntryTabLock))return;
#else
 NdisAllocateSpinLock(pAd,&pAd->ApCfg.FtTab.FT_R1khEntryTabLock);
#endif''',1)
    wrappers='''
BOOLEAN wr_ft_cache_initialize_checked(RTMP_ADAPTER *pAd)
{
 unsigned long serial;BOOLEAN ok;
 if(!pAd||!pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 serial=wr_ft_cache_start(&pAd->wr_ft_cache_lifetime);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!serial)return FALSE;
 wr_native_FT_R1khEntryTabInit(pAd);
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_publish(&pAd->wr_ft_cache_lifetime,serial,
  pAd->ApCfg.FtTab.FT_R1khEntryTabReady==TRUE);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return ok;
}
/* Caller serializes the entire AP lifecycle. Ticket is linear and must not
 * be copied, retried concurrently or abandoned after side effects begin. */
unsigned long wr_ft_cache_release_reserve(RTMP_ADAPTER *pAd)
{
 unsigned long serial=0;
 if(!pAd||!pAd->wr_ft_cache_lifetime_initialized)return 0;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(wr_ft_cache_close(&pAd->wr_ft_cache_lifetime))
  serial=wr_ft_cache_destroy_begin(&pAd->wr_ft_cache_lifetime);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return serial;
}
BOOLEAN wr_ft_cache_release_reserved(RTMP_ADAPTER *pAd,unsigned long serial)
{
 BOOLEAN ok;
 if(!pAd||!serial||!pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_destroy_claim(&pAd->wr_ft_cache_lifetime,serial);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!ok)return FALSE;
 wr_native_FT_R1khEntryTabDestroy(pAd);
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_destroy_finish(&pAd->wr_ft_cache_lifetime,serial,
  pAd->ApCfg.FtTab.FT_R1khEntryTabReady==FALSE);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return ok;
}
BOOLEAN wr_ft_cache_release_checked(RTMP_ADAPTER *pAd)
{
 unsigned long serial=wr_ft_cache_release_reserve(pAd);
 return serial?wr_ft_cache_release_reserved(pAd,serial):FALSE;
}

'''
    return '\n'.join(bodies)+wrappers


def compose_map(changes,src):
    """Add checked entry points and declarations to the same prepared TUs.

    Native FT_Init/Release stay unchanged until all AP/KDP callers are bound.
    """
    result=dict(changes)
    source=result.get('common/ft.c')
    header=result.get('include/ft.h')
    adapter=result.get('include/rtmp.h','')
    if source is None or header is None or 'wr_ft_cache_lifetime_initialized;' not in adapter:
        raise ValueError('checked lifecycle requires prepared cache source/header/storage')
    if 'wr_ft_cache_initialize_checked(' in header:
        raise ValueError('checked lifecycle declarations already composed')
    functions=compose(source)
    anchor='VOID FT_Init('
    if header.count(anchor)!=1:raise ValueError('native FT init declaration changed')
    declarations='''BOOLEAN wr_ft_cache_initialize_checked(RTMP_ADAPTER *);
BOOLEAN wr_ft_cache_release_checked(RTMP_ADAPTER *);
unsigned long wr_ft_cache_release_reserve(RTMP_ADAPTER *);
BOOLEAN wr_ft_cache_release_reserved(RTMP_ADAPTER *,unsigned long);
'''
    result['common/ft.c']=source+'\n#ifdef DOT11R_FT_SUPPORT\n'+functions+'\n#endif\n'
    result['include/ft.h']=header.replace(anchor,declarations+anchor,1)
    return result
