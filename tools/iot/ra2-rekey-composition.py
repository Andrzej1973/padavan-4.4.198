"""Scope the independent GTK timer to the existing ra2 control-user fence."""
import re

GUARD = '#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
WRAPPER = r'''
static VOID wr_iot_grekey_periodic_raw(PVOID,PVOID,PVOID,PVOID);
VOID GREKEYPeriodicExec(PVOID s1,PVOID context,PVOID s2,PVOID timer)
{
'''+GUARD+r'''
 RTMP_ADAPTER *ad=(RTMP_ADAPTER *)context;
 /* Match the exact third timer; never alter Main/Guest callback semantics. */
 if(ad&&IS_MT7603(ad)&&timer==&ad->ApCfg.MBSSID[2].REKEYTimer){
  ULONG flags=0;int admitted=0;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  if(!ad->wr_iot_ra2_key_active&&ad->ApCfg.BssidNum==3&&
     ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))
   admitted=wr_iot_ra2_rekey_admit(&ad->wr_iot_driver_owner,
    &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
    ad->net_dev,ad->ApCfg.MBSSID[2].wdev.if_dev,VIRTUAL_IF_NUM(ad),
    &ad->wr_iot_control_users,&ad->wr_iot_control_poisoned,
    ad->wr_iot_boot_active||ad->wr_iot_boot_failed||
    ad->wr_iot_close_owner.active||ad->wr_iot_closed_probe.active);
  if(admitted)ad->wr_iot_ra2_key_active=1;
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(admitted){
   wr_iot_grekey_periodic_raw(s1,context,s2,timer);
   RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
   if(ad->wr_iot_ra2_key_active==1)ad->wr_iot_ra2_key_active=0;
   else ad->wr_iot_control_poisoned=1;
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
   wr_iot_control_leave(ad);
  }
  /* Leave countdown/key state untouched on refusal. The existing repeating
   * timer owns the next tick; no new timer, loop or global key reset. */
  return;
 }
#endif
 wr_iot_grekey_periodic_raw(s1,context,s2,timer);
}
static VOID wr_iot_grekey_periodic_raw(PVOID SystemSpecific1,
 PVOID FunctionContext,PVOID SystemSpecific2,PVOID SystemSpecific3)
'''


def compose(text):
    signature = (r'VOID GREKEYPeriodicExec\(\s*IN PVOID SystemSpecific1,\s*'
                 r'IN PVOID FunctionContext,\s*IN PVOID SystemSpecific2,\s*'
                 r'IN PVOID SystemSpecific3\)\s*(?=\{)')
    if 'wr_iot_grekey_periodic_raw' in text:
        raise ValueError('ra2 rekey wrapper already installed')
    matches = list(re.finditer(signature, text))
    if len(matches) != 1:
        raise ValueError('Native GREKEY callback signature changed')
    match = matches[0]
    return (text[:match.start()] + GUARD + '\n#include "ra2-rekey-admission.h"\n#endif\n' +
            WRAPPER + text[match.end():])
