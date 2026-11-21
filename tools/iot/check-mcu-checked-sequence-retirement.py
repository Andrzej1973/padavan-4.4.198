#!/usr/bin/env python3
"""Exercise checked-ID retirement against the extracted actual ACK dispatcher."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-checked-id-retirement-') as td:
 c=Path(td)/'check.c'
 subprocess.run(['python3',str(here/'prepare-mcu-result-check.py'),str(a.candidate),str(c)],check=True)
 s='#include "mcu-sequence-reservation.h"\n'+c.read_text()
 pos=s.index(' puts("PASS extracted checked ACK branch:')
 s=s[:pos]+r'''
 struct wr_iot_mcu_sequence_reservation ledger={0};
 unsigned first=wr_iot_mcu_sequence_reserve_checked(&ledger);assert(first==1);
 assert(wr_iot_mcu_sequence_finish(&ledger,first,0));
 assert(!ledger.occupied&&!ledger.quarantined&&ledger.retired==(1u<<first));
 for(unsigned i=0;i<30;i++){
  unsigned current=wr_iot_mcu_sequence_reserve(&ledger);assert(current&&current!=first);
  msg=base;msg.seq=current;ev.fw_rxd_1.field.seq_num=first;
  dispatch(&msg,&ev,&pkt);
  assert(!msg.ack_done&&msg.wr_iot_firmware_result==1);
  assert(wr_iot_mcu_sequence_finish(&ledger,current,0));
 }
 for(unsigned i=0;i<14;i++){
  unsigned current=wr_iot_mcu_sequence_reserve_checked(&ledger);assert(current&&current!=first);
  assert(wr_iot_mcu_sequence_finish(&ledger,current,0));
 }
 assert(ledger.retired==0xfffeU&&!ledger.quarantined&&!ledger.poisoned&&!ledger.occupied);
 assert(!wr_iot_mcu_sequence_reserve(&ledger)&&!wr_iot_mcu_sequence_reserve_checked(&ledger));
 ledger=(struct wr_iot_mcu_sequence_reservation){0};
 unsigned timed=wr_iot_mcu_sequence_reserve_checked(&ledger);
 assert(wr_iot_mcu_sequence_finish(&ledger,timed,1));
 assert(ledger.retired==(1u<<timed)&&ledger.quarantined==(1u<<timed));
 unsigned other=wr_iot_mcu_sequence_reserve(&ledger);assert(other&&other!=timed);
 assert(wr_iot_mcu_sequence_finish(&ledger,other,0));
 assert(ledger.quarantined==(1u<<timed));
 assert(!wr_iot_mcu_sequence_release(&ledger,other)&&ledger.poisoned);
 assert(!wr_iot_mcu_sequence_reserve_checked(&ledger));
 puts("PASS actual checked ACK branch rejects successful old ACK across30 allocations; checked pool exhausts without reuse; timeout quarantine and poison remain independent; no epoch reset/runtime proof");
'''+s[pos:]
 c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
