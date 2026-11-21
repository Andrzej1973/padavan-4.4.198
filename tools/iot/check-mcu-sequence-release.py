#!/usr/bin/env python3
"""Exercise generated adapter-release gate against leftover ID reservations."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(here/'check-mcu-sender-release.c').read_text().replace('#include "mcu-sender-owner.h"','#include "mcu-sender-owner.h"\n#include "mcu-sequence-reservation.h"')
s=s.replace('struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;','struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;struct wr_iot_mcu_sequence_reservation wr_iot_sequence;')
s=s.replace('#include "mcu-sender-release.inc"','#include "'+str((a.candidate/'include/wr-iot-mcu-sender-release.inc').resolve())+'"')
s=s.replace(' wr_iot_mcu_sender_init(s);assert(wr_iot_mcu_sender_enter(s));',''' a.wr_iot_sequence.occupied=2;
 assert(wr_iot_mcu_sender_release_begin(&a)==-1&&!held&&!s->release_claimed);
 a.wr_iot_sequence.occupied=0;a.wr_iot_sequence.poisoned=1;
 assert(wr_iot_mcu_sender_release_begin(&a)==-1&&!held&&!s->release_claimed);
 a.wr_iot_sequence.poisoned=0;
 wr_iot_mcu_sender_init(s);assert(wr_iot_mcu_sender_enter(s));''')
with tempfile.TemporaryDirectory(prefix='wr-seq-release-') as d:
 c=Path(d)/'check.c';c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS generated release refuses leftover/poisoned reservation independent of message count')
