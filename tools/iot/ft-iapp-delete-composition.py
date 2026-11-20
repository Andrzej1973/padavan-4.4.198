"""Prepare request retirement before native delete publication withdrawal."""
def compose(changes,src,local):
    result=dict(changes)
    header=result.get('include/rtmp.h','')
    if 'struct wr_ft_iapp_request_state wr_ft_iapp_requests;' not in header:
        raise ValueError('FT delete retirement requires adapter request registry')
    source=result.get('mgmt/mgmt_entrytb.c','')
    if 'wr_ft_iapp_slot_retire_locked' in source:
        raise ValueError('FT delete retirement already prepared')
    anchor=''' if (MAC_ADDR_EQUAL(pEntry->Addr,pAddr)) {
  WRITE_ONCE(pAd->wr_assoc_visible[wcid],0); smp_wmb();
 }'''
    if source.count(anchor)!=1:raise ValueError('FT delete retirement anchor changed')
    source=source.replace(anchor,''' if (MAC_ADDR_EQUAL(pEntry->Addr,pAddr)) {
#ifdef DOT11R_FT_SUPPORT
  if(!wr_ft_iapp_slot_retire_locked(pAd,&pAd->wr_ft_iapp_requests,wcid)){
   NdisReleaseSpinLock(&pAd->MacTabLock);return FALSE;
  }
#endif
  WRITE_ONCE(pAd->wr_assoc_visible[wcid],0); smp_wmb();
 }''',1)
    include='#include <rt_config.h>'
    if source.count(include)!=1:raise ValueError('FT delete include anchor changed')
    source=source.replace(include,include+'\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-iapp-slot-retirement.h"\n#endif',1)
    result['mgmt/mgmt_entrytb.c']=source
    result['include/ft-iapp-slot-retirement.h']=(local/'ft-iapp-slot-retirement.h').read_text()
    return result


def compose_reassociate(changes,src,local):
    result=dict(changes)
    if 'struct wr_ft_iapp_request_state wr_ft_iapp_requests;' not in result.get('include/rtmp.h',''):
        raise ValueError('FT reassociation retirement requires adapter request registry')
    kernel=result.get('include/assoc-generation-kernel.h','')
    if 'wr_ft_iapp_slot_retire_locked' in kernel:
        raise ValueError('FT reassociation retirement already prepared')
    anchor='  generation = wr_assoc_generation_next(&ad->wr_assoc_generations[entry->wcid]);'
    if kernel.count(anchor)!=1:raise ValueError('FT reassociation generation anchor changed')
    kernel=kernel.replace(anchor,'''#ifdef DOT11R_FT_SUPPORT
  if(entry!=&ad->MacTab.Content[entry->wcid]||
     !wr_ft_iapp_slot_retire_locked(ad,&ad->wr_ft_iapp_requests,entry->wcid)){
   NdisReleaseSpinLock(&ad->MacTabLock);return 0;
  }
#endif
'''+anchor,1)
    kernel='#ifdef DOT11R_FT_SUPPORT\n#include "ft-iapp-slot-retirement.h"\n#endif\n'+kernel
    result['include/assoc-generation-kernel.h']=kernel
    result['include/ft-iapp-slot-retirement.h']=(local/'ft-iapp-slot-retirement.h').read_text()
    return result
