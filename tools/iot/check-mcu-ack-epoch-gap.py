#!/usr/bin/env python3
"""Reproduce known stale ACK ambiguity; success means gap reproduced, not acceptance."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-ack-epoch-gap-') as d:
 c=Path(d)/'check.c'
 subprocess.run(['python3',str(here/'prepare-mcu-result-check.py'),str(a.candidate),str(c)],check=True)
 s=c.read_text();s='#include "mcu-sequence-reservation.h"\n'+s
 anchor=' puts("PASS extracted checked ACK branch:'
 pos=s.index(anchor)
 s=s[:pos]+r'''
 /* Complete and destroy 15 prior messages; firmware may still deliver a
  * duplicate of the first result. Host ledger is empty between messages. */
 struct wr_iot_mcu_sequence_reservation ledger={0};
 unsigned first=wr_iot_mcu_sequence_reserve(&ledger);assert(first==1);
 assert(wr_iot_mcu_sequence_release(&ledger,first));
 for(unsigned i=0;i<14;i++){
  unsigned slot=wr_iot_mcu_sequence_reserve(&ledger);assert(slot);
  assert(wr_iot_mcu_sequence_release(&ledger,slot));
 }
 unsigned reused=wr_iot_mcu_sequence_reserve(&ledger);assert(reused==first);
 msg=base;msg.seq=reused;ev.fw_rxd_1.field.seq_num=first;
 /* Same command/status envelope as old ON result; payload has no ON/OFF echo. */
 dispatch(&msg,&ev,&pkt);
 assert(msg.wr_iot_firmware_result==0&&msg.ack_done==1);
 puts("KNOWN GAP REPRODUCED: old matching ACK accepted after 15-slot reuse; host reservation is not firmware epoch proof");
 /* Controller init resets cmd_seq to zero. A fresh host allocation also
  * clears its reservation ledger. Neither operation changes a wire event:
  * absent a proven RX/firmware boundary, the previous seq=1 still matches. */
 ledger=(struct wr_iot_mcu_sequence_reservation){0};
 reused=wr_iot_mcu_sequence_reserve(&ledger);assert(reused==first);
 msg=base;msg.seq=reused;ev.fw_rxd_1.field.seq_num=first;
 dispatch(&msg,&ev,&pkt);
 assert(msg.wr_iot_firmware_result==0&&msg.ack_done==1);
 puts("KNOWN GAP REPRODUCED: host-only controller/ledger reset does not establish an ACK epoch boundary");
 /* Timeout IDs remain quarantined across subsequent sequence wraps.
  * Exercise the actual extracted dispatcher, not just mask arithmetic. */
 ledger=(struct wr_iot_mcu_sequence_reservation){0};
 first=wr_iot_mcu_sequence_reserve(&ledger);
 assert(wr_iot_mcu_sequence_finish(&ledger,first,1));
 for(unsigned i=0;i<30;i++){
  unsigned current=wr_iot_mcu_sequence_reserve(&ledger);
  assert(current&&current!=first);
  msg=base;msg.seq=current;ev.fw_rxd_1.field.seq_num=first;
  dispatch(&msg,&ev,&pkt);
  assert(!msg.ack_done&&msg.wr_iot_firmware_result==1);
  assert(wr_iot_mcu_sequence_finish(&ledger,current,0));
 }
 puts("PASS timeout quarantine: late timed-out ACK never completes a subsequent command across wraps; successful-reply duplicate gap remains");
 return 0;
}
'''
 c.write_text(s)
 # This negative control intentionally uses the old unretired model and a
 # fresh host ledger. Keep its wire-ambiguity assertions independent of the
 # protected candidate allocator exercised by checked-sequence-retirement.
 if 'wr_iot_mcu_sequence_reserve_checked' in (a.candidate/'include/mcu-sequence-reservation.h').read_text():
  s=s.replace('KNOWN GAP REPRODUCED:', 'NEGATIVE CONTROL (checked-ID policy bypassed):')
  s=s.replace('successful-reply duplicate gap remains', 'wire ambiguity still requires a verified ledger-reset boundary')
  c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
