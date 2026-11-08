#!/usr/bin/env python3
"""Execute the actual composed recovery-idle function with kernel dependencies stubbed."""
from pathlib import Path
import ast, runpy, subprocess, tempfile
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'close-owner-composition.py'))['compose_recovery_idle']
source=(here/'mbss-recovery-work.inc').read_text()
changed=compose(source)
try:
 compose(changed)
except ValueError:
 pass
else:
 raise AssertionError('duplicate composition accepted')
start=changed.index('BOOLEAN wr_iot_mbss_recovery_idle_locked(')
end=changed.index('\n}',start)+2
fixture='''
#include <assert.h>
typedef int BOOLEAN;
typedef unsigned int UINT;
#define TRUE 1
#define FALSE 0
#define WDEV_NUM_MAX 2
#include "driver-api-close-owner.h"
struct work { int work; };
typedef struct { struct wr_iot_driver_close_owner wr_iot_close_owner; int wr_iot_mbss_recovery[3]; struct work wr_iot_mbss_work[3]; } RTMP_ADAPTER;
static int wr_iot_mbss_recovery_storage_idle(int *r,unsigned n){for(unsigned i=0;i<n;i++)if(r[i])return 0;return 1;}
static int work_busy(int *w){return *w;}
'''+changed[start:end]+'''
int main(void){
 RTMP_ADAPTER ad={0};
 assert(!wr_iot_mbss_recovery_idle_locked(0));
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
 ad.wr_iot_close_owner.active=1;
#ifdef MT7603
 assert(!wr_iot_mbss_recovery_idle_locked(&ad));
#else
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
#endif
 /* A complete module handoff retires only lifetime, never active OPEN fence. */
 ad.wr_iot_close_owner.retirement_module_transferred=1;
#ifdef MT7603
 assert(!wr_iot_mbss_recovery_idle_locked(&ad));
#endif
 ad.wr_iot_close_owner.consumed=1;
 ad.wr_iot_close_owner.recovery_netdev_transferred=1;
 ad.wr_iot_close_owner.recovery_netdev_returned=1;
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
 assert(ad.wr_iot_close_owner.active);
#ifdef MT7603
 struct wr_iot_driver_close_owner ready=ad.wr_iot_close_owner;
 for(unsigned fault=0;fault<13;fault++){
  ad.wr_iot_close_owner=ready;
  switch(fault){
   case 0:ad.wr_iot_close_owner.module_held=1;break;
   case 1:ad.wr_iot_close_owner.retirement_task=&ad;break;
   case 2:ad.wr_iot_close_owner.task=&ad;break;
   case 3:ad.wr_iot_close_owner.netdev_held=1;break;
   case 4:ad.wr_iot_close_owner.retirement_started=1;break;
   case 5:ad.wr_iot_close_owner.retirement_entered=1;break;
   case 6:ad.wr_iot_close_owner.retirement_canceling=1;break;
   case 7:ad.wr_iot_close_owner.consumed=0;break;
   case 8:ad.wr_iot_close_owner.recovery_netdev_transferred=0;break;
   case 9:ad.wr_iot_close_owner.recovery_join_pending=1;break;
   case 10:ad.wr_iot_close_owner.recovery_netdev_returned=0;break;
   case 11:ad.wr_iot_close_owner.retirement_module_transferred=0;break;
   case 12:ad.wr_iot_close_owner.retirement_handle=&ad;break;
  }
  assert(!wr_iot_mbss_recovery_idle_locked(&ad));
 }
 ad.wr_iot_close_owner=ready;
#endif
 for(unsigned i=0;i<3;i++){
  ad.wr_iot_mbss_recovery[i]=1;assert(!wr_iot_mbss_recovery_idle_locked(&ad));ad.wr_iot_mbss_recovery[i]=0;
  ad.wr_iot_mbss_work[i].work=1;assert(!wr_iot_mbss_recovery_idle_locked(&ad));ad.wr_iot_mbss_work[i].work=0;
 }
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-close-lifetime-') as tmp:
 src=Path(tmp)/'check.c';out=Path(tmp)/'check';src.write_text(fixture)
 for defines in [[],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']]:
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*defines,str(src),'-o',str(out)],check=True)
  subprocess.run([str(out)],check=True)
# Execute the inner reaper's actual tail, which deliberately bypasses public idle.
join_compose=runpy.run_path(str(here/'close-owner-composition.py'))['compose_recovery_join']
join_source=(here/'mbss-recovery-join.inc').read_text()
old=' ready=wr_iot_mbss_recovery_idle_locked(ad);'
reaper_ast=ast.parse((here/'prepare-mbss-reaper-gate.py').read_text())
replacements=[ast.literal_eval(node.args[2]) for node in ast.walk(reaper_ast)
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='one'
 and len(node.args)==3 and isinstance(node.args[1],ast.Constant) and node.args[1].value==old]
assert len(replacements)==1
replacement=replacements[0]
assert join_source.count(old)==1
joined=join_compose(join_source.replace(old,replacement))
try:
 join_compose(joined)
except ValueError:
 pass
else:
 raise AssertionError('duplicate join composition accepted')
tail=joined[joined.index(' ready=wr_iot_mbss_recovery_storage_idle'):joined.index(' RTMP_IRQ_UNLOCK',joined.index(' ready=wr_iot_mbss_recovery_storage_idle'))]
# Reuse adapter/work/storage fixtures and the same positive/fault assertions.
join_fixture=fixture[:fixture.index('BOOLEAN wr_iot_mbss_recovery_idle_locked(')]+"BOOLEAN wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad){ UINT slot; int ready; if(!ad)return 0;\n"+tail+" return ready; }\n"+fixture[fixture.index('int main(void)'):]
with tempfile.TemporaryDirectory(prefix='wr-close-join-') as tmp:
 src=Path(tmp)/'check.c';out=Path(tmp)/'check';src.write_text(join_fixture)
 for defines in [[],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']]:
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*defines,str(src),'-o',str(out)],check=True)
  subprocess.run([str(out)],check=True)
print('PASS actual composed lifetime fence: unresolved CLOSE retains adapter, legacy storage/work fences preserved, other targets unchanged; kernel integration/runtime unverified')
