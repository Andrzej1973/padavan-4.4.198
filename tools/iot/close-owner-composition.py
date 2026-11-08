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
