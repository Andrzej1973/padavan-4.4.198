#!/usr/bin/env python3
"""Exercise actual adapter release fence against per-slot MBSS owner states."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
init=(a.candidate/'common/rtmp_init.c').read_text()
assert 'wr_iot_mbss_recovery_init(&pAd->wr_iot_mbss_recovery[wr_iot_slot]);' in init
s=(here/'check-peer-adapter-release.c').read_text()
s=s.replace('#include "pci-retirement-owner.h"','#include "pci-retirement-owner.h"\n#include "mbss-recovery-storage.h"')
s=s.replace(' struct wr_child_teardown wr_iot_children;', ' struct wr_child_teardown wr_iot_children;\n struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX+1];')
s=s.replace(' memset(a,0,sizeof *a);current=a;', ' memset(a,0,sizeof *a);current=a;\n for(unsigned int i=0;i<WDEV_NUM_MAX+1;i++)wr_iot_mbss_recovery_init(&a->wr_iot_mbss_recovery[i]);')
marker='int main(void){RTMP_ADAPTER a;';assert s.count(marker)==1
s=s.replace(marker,marker+r'''
 for(unsigned int slot=0;slot<WDEV_NUM_MAX+1;slot++){
  ready(&a);a.wr_iot_mbss_recovery[slot].phase=WR_MBSS_OWNER_QUEUED;
  a.wr_iot_mbss_recovery[slot].deferred_owners=1;
  assert(!wr_iot_adapter_release_begin(&a)&&!a.wr_iot_nettask_release_claimed&&!a.wr_iot_peer_table_owner.poisoned);
  ready(&a);a.wr_iot_mbss_recovery[slot].completed=1;
  assert(!wr_iot_adapter_release_begin(&a)&&!a.wr_iot_nettask_release_claimed);
  ready(&a);a.wr_iot_mbss_recovery[slot].device=&a;
  assert(!wr_iot_adapter_release_begin(&a));
  ready(&a);a.wr_iot_mbss_recovery[slot].deferred_owners=1;
  assert(!wr_iot_adapter_release_begin(&a));
 }
''')
with tempfile.TemporaryDirectory(prefix='wr-mbss-storage-check-') as d:
 c=Path(d)/'check.c';c.write_text(s)
 for flags in ([],['-DWSC_INCLUDED']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
  subprocess.run([d+'/check'],check=True)
print('PASS actual release helper: every MBSS slot fences release before permanent effects; baseline/WSC fixtures')
