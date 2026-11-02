#!/usr/bin/env python3
"""Run generated final-drop helper with message lifetime fault fixture."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
s=(here/'check-mcu-message-lifetime.c').read_text()
s=s.replace('#include "mcu-sender-owner.h"','#include "mcu-sender-owner.h"\n#include "mcu-sequence-reservation.h"')
s=s.replace('struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;','struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;struct wr_iot_mcu_sequence_reservation wr_iot_sequence;')
s=s.replace('RTMP_ADAPTER *ad;','RTMP_ADAPTER *ad;unsigned int slot;')
s=s.replace('m->ad=a;return m;','m->ad=a;m->slot=0;return m;')
s=s.replace('#include "mcu-message-lifetime.inc"','#include "'+str((a.candidate/'include/wr-iot-mcu-message-lifetime.inc').resolve())+'"')
s=s.replace('RTMP_ADAPTER *a=m->ad;free(m);a->counters++;wr_iot_mcu_message_drop(a);','RTMP_ADAPTER *a=m->ad;unsigned int slot=m->slot;free(m);a->counters++;wr_iot_mcu_message_drop(a,slot);')
s=s.replace('destroy(m);assert(a.counters==1', 'm->slot=wr_iot_mcu_sequence_reserve(&a.wr_iot_sequence);assert(m->slot&&a.wr_iot_sequence.occupied);\n destroy(m);assert(!a.wr_iot_sequence.occupied);assert(a.counters==1')
s=s.replace('retire_target=heap;destroy(m);','m->slot=wr_iot_mcu_sequence_reserve(&heap->wr_iot_sequence);assert(m->slot);retire_target=heap;destroy(m);')
s=s.replace('assert(wr_iot_mcu_sender_release_claim(&retire_target->wr_iot_mcu_sender_owner));','assert(!retire_target->wr_iot_sequence.occupied);assert(wr_iot_mcu_sender_release_claim(&retire_target->wr_iot_mcu_sender_owner));')
with tempfile.TemporaryDirectory(prefix='wr-sequence-lifetime-') as d:
 c=Path(d)/'check.c';c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS generated final-drop releases reservation before immediate adapter free; mock destructor ordering only')
