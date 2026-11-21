"""Prepare fresh-adapter cache lifetime storage; never installs a producer.

Final adapter release/quiescence and native cache start/stop remain unbound.
The initialized flag is immutable after successful fresh allocation until final
adapter retirement, which must separately exclude every callback before free.
"""
INITIALIZE = '''
 pAd->wr_ft_ap_stop_owner=(struct wr_ft_ap_stop_owner){0};
 wr_ft_cache_lifetime_init(&pAd->wr_ft_cache_lifetime);
 pAd->wr_ft_cache_lifetime_initialized=FALSE;
#ifdef OS_ABL_FUNC_SUPPORT
 if(NdisAllocateSpinLock(pAd,&pAd->wr_ft_cache_lifetime_lock))
  pAd->wr_ft_cache_lifetime_initialized=TRUE;
 else
  pAd->wr_ft_cache_lifetime.owner.poisoned=1;
#else
 NdisAllocateSpinLock(pAd,&pAd->wr_ft_cache_lifetime_lock);
 pAd->wr_ft_cache_lifetime_initialized=TRUE;
#endif
'''


def compose(changes, local):
    result=dict(changes)
    header=result.get('include/rtmp.h','')
    init=result.get('common/rtmp_init.c','')
    if 'wr_ft_cache_lifetime' in header or 'wr_ft_cache_lifetime_init(' in init:
        raise ValueError('cache lifetime storage already composed')
    include='#include "ft-iapp-request-state.h"'
    field=' struct wr_ft_iapp_request_state wr_ft_iapp_requests;'
    anchor=' wr_ft_pending_ledger_init(&pAd->wr_ft_pending);'
    for text,old in ((header,include),(header,field),(init,anchor)):
        if text.count(old)!=1:
            raise ValueError('cache storage requires exact fresh adapter predecessor')
    # Verify that predecessor init is inside the native fresh-allocation path,
    # after resource-list initialization and before the OS cookie is published.
    start=init.index('NDIS_STATUS RTMPAllocAdapterBlock(')
    end=init.index('\n}',start)+2
    body=init[start:end]
    if not (body.index('initList(&pAd->RscLockMemList);') <
            body.index(anchor) < body.index('pAd->OS_Cookie = handle;')):
        raise ValueError('cache storage initialization lifetime changed')
    header=header.replace(include,include+'\n#include "ft-cache-lifetime.h"\n#include "ft-ap-stop-owner.h"',1)
    header=header.replace(field,field+'\n struct wr_ft_ap_stop_owner wr_ft_ap_stop_owner;\n struct wr_ft_cache_lifetime wr_ft_cache_lifetime;\n'
        ' NDIS_SPIN_LOCK wr_ft_cache_lifetime_lock;\n'
        ' BOOLEAN wr_ft_cache_lifetime_initialized;',1)
    init=init.replace(anchor,anchor+'\n'+INITIALIZE,1)
    result['include/rtmp.h']=header;result['common/rtmp_init.c']=init
    for name in ('ft-cache-lifetime.h','peer-table-owner.h','ft-ap-stop-owner.h','ft-ap-cache-reservation.h'):
        result['include/'+name]=(local/name).read_text()
    return result
