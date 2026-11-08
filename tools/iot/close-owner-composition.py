"""Apply only the reviewed optional CLOSE-owner handoff to checked begin_close."""

def compose(text):
 anchor='/* Candidate: sole owner of CLOSE/BSS_CLOSE ticket pins all lifetimes.'
 call=' if(!ad||ad->net_dev==dev)return -1;\n RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);'
 if text.count(anchor)!=1 or text.count(call)<1 or 'wr_iot_driver_close_take_bound' in text:
  raise ValueError('Checked CLOSE handoff source anchor changed')
 # Only the first occurrence is begin_close, not the executor/recovery path.
 start=text.index('INT wr_iot_mbss_begin_close(')
 stop=text.index('/* Caller holds the common adapter lock.',start)
 begin=text[start:stop]
 if begin.count(call)!=1:raise ValueError('Ambiguous begin-close handoff anchor')
 guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
 begin=begin.replace(call,''' if(!ad||ad->net_dev==dev)return -1;
'''+guard+'''
 {
  int handoff=wr_iot_driver_close_take_bound(ad,dev,ticket,generation);
  if(handoff<=0)return handoff;
 }
#endif
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);''',1)
 return guard+'\n#include "driver-api-close-binding.inc"\n#endif\n'+text[:start]+begin+text[stop:]

def compose_recovery_idle(text):
 """Retain adapter lifetime while an API CLOSE owner remains unresolved."""
 anchor=' UINT slot;\n if(!ad||'
 start=text.index('BOOLEAN wr_iot_mbss_recovery_idle_locked(')
 end=text.index('\n}',start)+2
 body=text[start:end]
 if body.count(anchor)!=1 or 'wr_iot_close_owner.active' in text:
  raise ValueError('Recovery idle CLOSE-owner fence anchor changed')
 body=body.replace(anchor,''' UINT slot;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 /* Reference-only completion does not retire the API lifetime owner. */
 if(ad && ad->wr_iot_close_owner.active)return FALSE;
#endif
 if(!ad||''',1)
 return text[:start]+body+text[end:]

def compose_recovery_join(text):
 """The exclusive reaper bypasses public idle; preserve CLOSE fence there too."""
 anchor=' ready=wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1);'
 if text.count(anchor)!=1 or 'wr_iot_close_owner.active' in text:
  raise ValueError('Recovery join CLOSE-owner fence anchor changed')
 return text.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(ad->wr_iot_close_owner.active)ready=0;
#endif''',1)
