#!/usr/bin/env python3
"""Exercise actual composed public retirement function and join fence."""
from pathlib import Path
import ast,runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'initial-idle-lifetime-composition.py'))
previous=runpy.run_path(str(here/'close-owner-composition.py'))
work=previous['compose_recovery_idle']((here/'mbss-recovery-work.inc').read_text())
join=(here/'mbss-recovery-join.inc').read_text()
tree=ast.parse((here/'prepare-mbss-reaper-gate.py').read_text())
for node in ast.walk(tree):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='one' and len(node.args)==3:
        if isinstance(node.args[1],ast.Constant) and node.args[1].value==' ready=wr_iot_mbss_recovery_idle_locked(ad);':
            old,new=ast.literal_eval(node.args[1]),ast.literal_eval(node.args[2]);assert join.count(old)==1;join=join.replace(old,new)
join=previous['compose_recovery_join'](join)
work,join=compose['retirement'](work,join)
try:compose['retirement'](work,join)
except ValueError:pass
else:raise AssertionError('Duplicate retirement transformation accepted')
header='#include "mbss-closed-probe.h"\n struct wr_iot_mbss_closed_probe wr_iot_closed_probe;'
init='NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));'
header,init=compose['storage'](header,init)
assert header.count('struct wr_iot_precreated_idle_probe wr_iot_idle_probe;')==1
assert init.count('NdisZeroMemory(&pAd->wr_iot_idle_probe')==1
try:compose['storage'](header,init)
except ValueError:pass
else:raise AssertionError('Duplicate storage transformation accepted')
start=work.index('BOOLEAN wr_iot_mbss_recovery_idle_locked(');end=work.index('\n}',start)+2
probe='''
#include <assert.h>
#include <stdio.h>
#include "driver-api-close-owner.h"
typedef int BOOLEAN;
typedef unsigned int UINT;
#define TRUE 1
#define FALSE 0
#define WDEV_NUM_MAX 2
struct work {int work;};
typedef struct {struct wr_iot_driver_close_owner wr_iot_close_owner;struct {int active;} wr_iot_idle_probe;int wr_iot_mbss_recovery[3];struct work wr_iot_mbss_work[3];} RTMP_ADAPTER;
static int wr_iot_mbss_recovery_storage_idle(int *r,unsigned n){for(unsigned i=0;i<n;i++)if(r[i])return 0;return 1;}
static int work_busy(int *w){return *w;}
'''+work[start:end]+'''
int main(void){
 RTMP_ADAPTER ad={0};
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
 ad.wr_iot_idle_probe.active=1;
#ifdef MT7603
 assert(!wr_iot_mbss_recovery_idle_locked(&ad));
#else
 assert(wr_iot_mbss_recovery_idle_locked(&ad));
#endif
 ad.wr_iot_idle_probe.active=0;assert(wr_iot_mbss_recovery_idle_locked(&ad));
 puts("PASS composed initial-idle retirement fence; Main/other compile guards retained");return 0;
}
'''
# The same reviewed predicate is inserted into the reaper join route.
assert 'if(ad->wr_iot_idle_probe.active ||\n    wr_iot_driver_close_blocks_adapter_retirement' in join
with tempfile.TemporaryDirectory(prefix='iot-idle-lifetime-') as d:
    source=Path(d)/'check.c';source.write_text(probe)
    for target in (False,True):
        out=Path(d)/str(target)
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*(['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT'] if target else []),'-I'+str(here),str(source),'-o',str(out)],check=True)
        subprocess.run([str(out)],check=True)
print('PASS storage/init composition and duplicate refusal; reaper join fence source checked, full target pending')
