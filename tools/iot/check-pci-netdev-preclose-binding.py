#!/usr/bin/env python3
"""Exercise actual preclose/drain ordering and bounded noncompletion refusal."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
s=(a.candidate/'os/linux/pci_main_dev.c').read_text()
start=s.index('static int wr_iot_pci_recovery_drain(');end=s.index('\n#include "wr-iot-pci-child-snapshot.inc"',start)
helper=s[start:end]
assert helper.index('wr_iot_pci_netdev_preclose(')<helper.index('flush_delayed_work(')<helper.index('wr_iot_pci_retirement_drain_complete(')
remove=s[s.index('static VOID DEVEXIT rt_pci_remove('):]
assert remove.index('if (!wr_iot_pci_recovery_drain(adapter))')<remove.index('wr_iot_terminal_command_join_checked(adapter)')<remove.index('wr_iot_pci_retirement_stop_requested(')
fixture=(here/'check-pci-recovery-drain.c').read_text()
fixture=fixture.replace(' int wr_iot_transition_lock;', ' int wr_iot_transition_lock;\n void *net_dev;\n struct {unsigned int deferred_owners;} wr_iot_aux_family_retry;\n struct work_struct wr_iot_aux_family_retry_work;')
fixture=fixture.replace('#include "pci-recovery-drain.inc"', '''
#define WDEV_NUM_MAX 3
#define WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS (WDEV_NUM_MAX + 4U)
#define NDIS_STATUS_SUCCESS 0
static int wr_iot_pci_netdev_preclose(RTMP_ADAPTER *ad,void *dev){
 assert(ad&&!locked);(void)dev;
 if(mode==5)return -1;
 if(mode==4&&flushes==0)return -1;
 return 0;
}
'''+helper)
fixture=fixture.replace('assert(flushes==4&&!locked&&','assert(flushes==WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS+1&&!locked&&')
fixture=fixture.replace(' puts("PASS isolated PCI drain:', ''' setup(&ad,4);ad.wr_iot_main_recovery.deferred_owners=0;ad.wr_iot_main_recovery_reap_work.work.pending=0;
 assert(wr_iot_pci_recovery_drain(&ad)&&flushes==2&&ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINED);
 setup(&ad,5);ad.wr_iot_main_recovery.deferred_owners=0;ad.wr_iot_main_recovery_reap_work.work.pending=0;
 assert(!wr_iot_pci_recovery_drain(&ad)&&flushes==WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS+1&&ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINING);
 puts("PASS isolated PCI drain:''')
if 'wr_iot_mbss_recovery_join_completed(adapter)' in helper:
 assert helper.index('wr_iot_mbss_recovery_join_completed(adapter)')<helper.index('RTMP_IRQ_LOCK(')<helper.index('wr_iot_pci_retirement_drain_next(')
 mock=r'''
static int mbss_join_calls;
static int wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad){
 assert(ad&&!locked);mbss_join_calls++;
 return mode==6?-1:0;
}
static int wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad){
 assert(ad&&locked&&mbss_join_calls);
 return mode!=7;
}
'''
 fixture=fixture.replace(helper,mock+helper)
 marker=' puts("PASS isolated PCI drain:'
 assert fixture.count(marker)==1
 fixture=fixture.replace(marker,r'''
 for(int fault=6;fault<=7;fault++){
  setup(&ad,fault);ad.wr_iot_main_recovery.deferred_owners=0;
  ad.wr_iot_main_recovery_reap_work.work.pending=0;mbss_join_calls=0;
  assert(!wr_iot_pci_recovery_drain(&ad)&&mbss_join_calls==1&&!locked);
  assert(ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINING);
 }
 setup(&ad,8);ad.wr_iot_main_recovery.deferred_owners=0;
 ad.wr_iot_main_recovery_reap_work.work.pending=0;mbss_join_calls=0;
 assert(wr_iot_pci_recovery_drain(&ad)&&mbss_join_calls==1&&!locked);
 assert(ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINED);
'''+marker)
with tempfile.TemporaryDirectory(prefix='wr-preclose-binding-check-') as tmp:
 c=Path(tmp)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',tmp+'/check'],check=True)
 subprocess.run([tmp+'/check'],check=True)
print('PASS actual preclose/drain: wait for joined close, refuse unresolved preclose, bounded retry, no premature DRAINED')
