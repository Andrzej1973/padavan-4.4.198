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
