"""Prepare deterministic EventGet output and detached-event cleanup only.

Not lifetime admission. Queue extraction and KDP teardown remain unbound.
"""
def compose(source,caller):
    signature='VOID TYPE_FUNC FT_KDP_EventGet('
    if source.count(signature)!=1:raise ValueError('EventGet definition changed')
    start=source.index(signature);end=source.index('\n}',start)+2
    native=source[start:end]
    if 'if(!pFtKdp)return;' in native:raise ValueError('EventGet already composed')
    anchor='{\n#ifndef FT_KDP_EMPTY'
    if native.count(anchor)!=1:raise ValueError('EventGet body changed')
    native=native.replace(anchor,'{\n if(!pFtKdp)return;\n *pFtKdp=NULL;\n#ifndef FT_KDP_EMPTY',1)
    declaration='FT_KDP_SIGNAL *pFtKdp;'
    free='FT_MEM_FREE(pAd, pFtKdp);'
    tail='\t\t\t\t\twrq->u.data.length = 0;\n\t\t\t\t}'
    if caller.count(declaration)!=1 or caller.count(free)!=1 or caller.count(tail)!=1:
        raise ValueError('EventGet caller cleanup anchors changed')
    caller=caller.replace(declaration,'FT_KDP_SIGNAL *pFtKdp=NULL;',1)
    caller=caller.replace(free,'/* detached event released after either output branch */',1)
    caller=caller.replace(tail,tail+'\n\t\t\t\tif(pFtKdp)FT_MEM_FREE(pAd,pFtKdp);',1)
    return native,caller


def compose_admission(native):
    signature='VOID TYPE_FUNC FT_KDP_EventGet('
    if native.count(signature)!=1 or '*pFtKdp=NULL;' not in native:
        raise ValueError('EventGet admission requires initialized output predecessor')
    if 'wr_ft_kdp_event_native(' in native:
        raise ValueError('EventGet admission already composed')
    native=native.replace(signature,'static VOID wr_ft_kdp_event_native(',1)
    return native+'''
VOID FT_KDP_EventGet(PRTMP_ADAPTER pAd,FT_KDP_SIGNAL **output)
{
 struct wr_ft_cache_lease lease={0};int admitted;
 if(!output)return;
 *output=NULL;
 if(!pAd||!pAd->wr_ft_cache_lifetime_initialized)return;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 admitted=wr_ft_cache_enter(&pAd->wr_ft_cache_lifetime,&lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!admitted)return;
 if(pAd->ApCfg.FtTab.FlgIsFtKdpInit==1&&pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK)
  wr_ft_kdp_event_native(pAd,output);
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 (void)wr_ft_cache_leave(&pAd->wr_ft_cache_lifetime,&lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
}
'''
