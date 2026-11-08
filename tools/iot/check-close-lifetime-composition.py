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
struct owner { unsigned int active; };
struct work { int work; };
typedef struct { struct owner wr_iot_close_owner; int wr_iot_mbss_recovery[3]; struct work wr_iot_mbss_work[3]; } RTMP_ADAPTER;
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
 ad.wr_iot_close_owner.active=0;
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
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',*defines,str(src),'-o',str(out)],check=True)
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
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',*defines,str(src),'-o',str(out)],check=True)
  subprocess.run([str(out)],check=True)
print('PASS actual composed lifetime fence: unresolved CLOSE retains adapter, legacy storage/work fences preserved, other targets unchanged; kernel integration/runtime unverified')
