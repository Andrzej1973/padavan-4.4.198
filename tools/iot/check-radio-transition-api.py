#!/usr/bin/env python3
"""Verify API transition extension differs from frozen historical asset only as reviewed."""
from pathlib import Path
here=Path(__file__).resolve().parent
expected=(here/'radio-transition.h').read_text()
def one(old,new):
 global expected
 if expected.count(old)!=1:raise SystemExit('Frozen transition anchor changed: '+repr(old[:70]))
 expected=expected.replace(old,new,1)
one('WR_RADIO_AUX_START};','WR_RADIO_AUX_START,WR_RADIO_BSS_OBSERVE};')
one('  }else if(operation==WR_RADIO_VERIFY){','  }else if(operation==WR_RADIO_BSS_OBSERVE){\n   if(s->phase!=WR_RADIO_READY||!s->main_ready||s->main_inhibited)return 0;\n  }else if(operation==WR_RADIO_VERIFY){')
one('/* Auxiliary (AP-client/WDS/monitor) open uses the same exclusive ticket but', '''/* End a read-only BSS observation. Preserve every current readiness/intent
 * bit, including reset/main-down that arrived while readback ran unlocked.
 * Retirement itself is not acceptance of the observed BSS state. */
static inline int wr_iot_radio_bss_observe_end(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t){
 if(!s||!t||t->operation!=WR_RADIO_BSS_OBSERVE||
    s->busy!=WR_RADIO_BSS_OBSERVE||s->serial!=t->serial)return 0;
 s->busy=0;s->retired_serial=t->serial;return 1;
}
/* Auxiliary (AP-client/WDS/monitor) open uses the same exclusive ticket but''')
one(' const struct wr_iot_radio_ticket *t,int observed_success){\n if(!s->epoch',' const struct wr_iot_radio_ticket *t,int observed_success){\n /* Pure BSS observation retires only via its non-mutating end helper. */\n if(t->operation==WR_RADIO_BSS_OBSERVE)return 0;\n if(!s->epoch')
if (here/'radio-transition-api.h').read_text()!=expected:
 raise SystemExit('API radio transition differs outside reviewed observation extension')
print('PASS API transition extension: frozen base unchanged; only reviewed BSS_OBSERVE additions')
