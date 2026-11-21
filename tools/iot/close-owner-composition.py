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
 if body.count(anchor)!=1 or 'wr_iot_driver_close_blocks_adapter_retirement' in text:
  raise ValueError('Recovery idle CLOSE-owner fence anchor changed')
 body=body.replace(anchor,''' UINT slot;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 /* Reference-only completion does not retire the API lifetime owner. */
 if(ad && wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))return FALSE;
#endif
 if(!ad||''',1)
 return text[:start]+body+text[end:]

def compose_recovery_join(text):
 """The exclusive reaper bypasses public idle; preserve CLOSE fence there too."""
 anchor=' ready=wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1);'
 if text.count(anchor)!=1 or 'wr_iot_driver_close_blocks_adapter_retirement' in text:
  raise ValueError('Recovery join CLOSE-owner fence anchor changed')
 return text.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))ready=0;
#endif''',1)

def compose_recovery_return(text):
 """Record the real dev_put boundary while the exclusive reaper pins adapter."""
 guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
 replacements=[
 ('  PNET_DEV dev=NULL;', '  PNET_DEV dev=NULL;\n'+guard+'\n  int api_claimed=0;\n  struct wr_iot_driver_close_join_receipt api_receipt={0};\n#endif'),
 ('    dev=(PNET_DEV)owner->device;', guard+'''
    if(ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.device==owner->device){
     api_claimed=wr_iot_driver_close_join_claim(&ad->wr_iot_close_owner,owner,r,1,&api_receipt);
     if(!api_claimed)goto api_join_unlock;
    }
#endif
    dev=(PNET_DEV)owner->device;'''),
 ('    if(!wr_iot_mbss_recovery_complete(owner,1))dev=NULL;', '''    if(!wr_iot_mbss_recovery_complete(owner,1)){
     dev=NULL;
'''+guard+'''
     if(api_claimed){ad->wr_iot_close_owner.recovery_join_pending=0;api_claimed=0;}
#endif
    }'''),
 ('  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);\n  if(dev)dev_put(dev);',guard+'''
api_join_unlock:
#endif
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(dev){
   dev_put(dev);
'''+guard+'''
   if(api_claimed){
    RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
    /* Failure retains the active API fence and pending receipt. */
    (void)wr_iot_driver_close_join_returned(&ad->wr_iot_close_owner,&api_receipt);
    RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
   }
#endif
  }''')]
 if 'api_join_unlock' in text:raise ValueError('Duplicate recovery return composition')
 for old,new in replacements:
  if text.count(old)!=1:raise ValueError('Recovery return anchor changed: '+old)
  text=text.replace(old,new,1)
 return guard+'\n#include "driver-api-close-join.h"\n#endif\n'+text
