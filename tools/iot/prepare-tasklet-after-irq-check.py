#!/usr/bin/env python3
"""Exercise both extracted close bodies with IRQ/tasklet order instrumentation."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('predecessor',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();base=a.output.with_name(a.output.name+'.base.c')
if a.output.exists() or base.exists():p.error('new fixture outputs required')
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-peer-close-executor-check.py')),
 str(a.predecessor),str(a.candidate),str(base)],check=True)
s=base.read_text()
anchor='static int ap_calls,pci_calls,radio_result=1,ap_result=1;'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\nstatic int irq_fenced=1,tasklet_joins,irq_releases;')
anchor='#define RTMP_OS_IRQ_RELEASE(ad,dev) ((void)(ad),(void)(dev))'
assert s.count(anchor)==1
s=s.replace(anchor,'#define RTMP_OS_IRQ_RELEASE(ad,dev) ((void)(ad),(void)(dev),assert(!held),irq_fenced=1,irq_releases++)')
anchor='#define RtmpNetTaskExit(ad) mock_nettask_exit(ad)'
assert s.count(anchor)==1
s=s.replace(anchor,'#define RtmpNetTaskExit(ad) ((void)(ad),assert(!held&&irq_fenced),tasklet_joins++)')
anchor='a->wr_iot_transition.phase=WR_RADIO_READY;'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'a->flags|=fRTMP_ADAPTER_INTERRUPT_IN_USE;irq_fenced=0;')
anchor='assert(a.wr_iot_peer_table_owner.closed&&competing_rejections>=8);'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'assert(tasklet_joins==1&&irq_releases==1);')
a.output.write_text(s,encoding='utf-8')
print('Instrumented actual close paths: IRQ release before tasklet kill, including join-failure retry')
