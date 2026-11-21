#!/usr/bin/env python3
"""Verify reviewed observation delta and apply it to accumulated candidate state."""
from pathlib import Path
TRANSFORMS = [('WR_RADIO_AUX_START};', 'WR_RADIO_AUX_START,WR_RADIO_BSS_OBSERVE};'),
 ('  }else if(operation==WR_RADIO_VERIFY){',
  '  }else if(operation==WR_RADIO_BSS_OBSERVE){\n'
  '   if(s->phase!=WR_RADIO_READY||!s->main_ready||s->main_inhibited)return 0;\n'
  '  }else if(operation==WR_RADIO_VERIFY){'),
 ('/* Auxiliary (AP-client/WDS/monitor) open uses the same exclusive ticket but',
  '/* End a read-only BSS observation. Preserve every current readiness/intent\n'
  ' * bit, including reset/main-down that arrived while readback ran unlocked.\n'
  ' * Retirement itself is not acceptance of the observed BSS state. */\n'
  'static inline int wr_iot_radio_bss_observe_end(struct wr_iot_radio_transition *s,\n'
  ' const struct wr_iot_radio_ticket *t){\n'
  ' if(!s||!t||t->operation!=WR_RADIO_BSS_OBSERVE||\n'
  '    s->busy!=WR_RADIO_BSS_OBSERVE||s->serial!=t->serial)return 0;\n'
  ' s->busy=0;s->retired_serial=t->serial;return 1;\n'
  '}\n'
  '/* Auxiliary (AP-client/WDS/monitor) open uses the same exclusive ticket but'),
 (' const struct wr_iot_radio_ticket *t,int observed_success){\n if(!s->epoch',
  ' const struct wr_iot_radio_ticket *t,int observed_success){\n'
  ' /* Pure BSS observation retires only via its non-mutating end helper. */\n'
  ' if(t->operation==WR_RADIO_BSS_OBSERVE)return 0;\n'
  ' if(!s->epoch')]
def extend_transition(base):
 expected=base
 for old,new in TRANSFORMS:
  if expected.count(old)!=1:
   raise SystemExit('Transition extension anchor changed: '+repr(old[:70]))
  expected=expected.replace(old,new,1)
 return expected
here=Path(__file__).resolve().parent
if (here/'radio-transition-api.h').read_text()!=extend_transition((here/'radio-transition.h').read_text()):
 raise SystemExit('API radio transition differs outside reviewed observation extension')
print('PASS API transition extension: frozen base unchanged; only reviewed BSS_OBSERVE additions')
