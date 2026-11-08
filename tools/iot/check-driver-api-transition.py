#!/usr/bin/env python3
"""Verify final API preserves all accumulated transition changes, not just base."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('parent',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args()
api=runpy.run_path(str(Path(__file__).with_name('check-radio-transition-api.py')))
parent=a.parent.read_text()
expected=api['extend_transition'](parent)
for name in ('radio-transition.h','radio-transition-api.h'):
 if (a.candidate/'include'/name).read_text()!=expected:
  raise SystemExit('Accumulated transition state lost or changed: '+name)
code='''#include <assert.h>
#include "radio-transition-api.h"
int main(void){
 struct wr_iot_radio_transition state;
 wr_iot_radio_transition_init(&state);
 assert(!state.mt_radio_off_stage&&!state.ap_cleanup_serial);
 assert(!state.close_body_serial&&!state.close_body_epoch);
 state.mt_radio_off_stage=2;state.ap_cleanup_serial=11;
 state.close_body_serial=12;state.close_body_epoch=13;
 state.phase=WR_RADIO_READY;state.main_ready=1;
 struct wr_iot_radio_ticket ticket;
 assert(wr_iot_radio_begin(&state,state.epoch,WR_RADIO_BSS_OBSERVE,&ticket));
 assert(wr_iot_radio_bss_observe_end(&state,&ticket));
 assert(state.mt_radio_off_stage==2&&state.ap_cleanup_serial==11);
 assert(state.close_body_serial==12&&state.close_body_epoch==13);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-api-transition-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS exact accumulated transition delta and shutdown/cleanup field regression')
