"""Exact reviewed join normalization for independently pinned candidate stages."""
import hashlib
from pathlib import Path

_DIAGNOSTIC_DECLARATIONS = b' unsigned int registry_result = 0, slot = 0, owned = 0, slot_phase = 0;\n unsigned int source = 0, phase = 0, busy = 0, stage = 0;\n unsigned int ticket_valid = 0, expected_vendor = 0;\n'
_DIAGNOSTIC_BLOCK = b' if (action == WR_MAIN_RECOVERY_CONTINUE_CLOSE)\n  ticket = owner->close_ticket;\n if (action == WR_MAIN_RECOVERY_NONE) {\n  source = owner->source;\n  phase = record ? record->phase : ~0U;\n  stage = record ? record->close_stage : 0;\n  expected_vendor = record ? record->close_vendor_count : 0;\n  ticket_valid = owner->close_ticket_valid;\n  busy = adapter->wr_iot_transition.busy;\n  registry_result = wr_iot_registry_count_check(adapter->wr_iot_interface_refs,\n   WDEV_NUM_MAX + 1, vendor_count, &slot, &owned);\n  if (slot < WDEV_NUM_MAX + 1)\n   slot_phase = adapter->wr_iot_interface_refs[slot].phase;\n }\n RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n if (action == WR_MAIN_RECOVERY_NONE)\n  printk_ratelimited(KERN_WARNING "MT7603 Main recovery admission refused: source=%u phase=%u busy=%u close_stage=%u ticket_valid=%u vendor=%u close_vendor=%u registry=%u slot=%u slot_phase=%u owned=%u\\n",\n   source, phase, busy, stage, ticket_valid, vendor_count, expected_vendor,\n   registry_result, slot, slot_phase, owned);'
_BASELINE_BLOCK = b' if (action == WR_MAIN_RECOVERY_CONTINUE_CLOSE)\n  ticket = owner->close_ticket;\n RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);'

def reviewed_predecessor(data,name):
 if name!='os/linux/rt_main_dev.c':return data
 if data.count(_DIAGNOSTIC_DECLARATIONS)==1 and data.count(_DIAGNOSTIC_BLOCK)==1:
  data=data.replace(_DIAGNOSTIC_DECLARATIONS,b'',1).replace(_DIAGNOSTIC_BLOCK,_BASELINE_BLOCK,1)
 marker=b'INT wr_iot_main_recovery_join_complete('
 if data.count(marker)!=1:return data
 start=data.index(marker);end=data.index(b'\n}',start)+2
 body=data[start:end]
 approved=('0d4b8abfeaf98c9f12564dc2d441c14b862796bc28f97a526e19902ef51022bb', '6dc2169771331e356b1c501c194f565b40bd5285b09a615d670ce642b4221da4')
 if hashlib.sha256(body).hexdigest() not in approved:return data
 baseline=Path(__file__).with_name('main-recovery-join-baseline.inc').read_bytes()
 if hashlib.sha256(baseline).hexdigest()!='5e24b03bc41930ea848f57991f95bd3918d472a6dc66c3906f382d71486c8c94':
  raise ValueError('changed reviewed main recovery join baseline')
 data=data[:start]+baseline+data[end:]
 marker=b'VOID wr_iot_main_recovery_reap_work_fn('
 if data.count(marker)!=1:return data
 start=data.index(marker);end=data.index(b'\n}',start)+2
 if hashlib.sha256(data[start:end]).hexdigest()!='94920f104135ea2650db70e639156549e21321100249c13b12abe6397cfa8126':return data
 baseline=Path(__file__).with_name('main-recovery-reaper-baseline.inc').read_bytes()
 if hashlib.sha256(baseline).hexdigest()!='14e51f936ce1484f139df0dce061edf031a2b1a9d1c6268bb1c9ca41dcb9598a':
  raise ValueError('changed reviewed main recovery reaper baseline')
 return data[:start]+baseline+data[end:]
