#!/usr/bin/env python3
"""Run the exact scoped refresh statement extracted from generated source."""
import argparse,ast,hashlib,runpy,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
api=runpy.run_path(str(here/'reserved-beacon-refresh.py'))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',nargs='?',type=Path);args=p.parse_args()
if args.driver:
 installed=(args.driver/'common/cmm_cfg.c').read_text()
 if installed.count(api['GUARDED'])!=1:raise SystemExit('Scoped refresh missing/ambiguous in final driver')
 original=installed.replace(api['GUARDED'],api['CALL'],1)
 if api['compose'](original)!=installed:raise SystemExit('Final driver scope differs from reviewed composition')
 print('Final dispatcher scoped refresh sha256='+hashlib.sha256(installed.encode()).hexdigest())

# Use actual generator's claimed branch instead of a second hand-written guard.
tree=ast.parse((here/'prepare-virtual-open-claim-candidate.py').read_text())
values=[ast.literal_eval(n.value).decode() for n in ast.walk(tree)
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='checked' for t in n.targets)]
assert len(values)==1
source=values[0]
# The actual claim-only successor removes the arithmetic fallback/comment.
# Reproduce that transformation from its reviewed generator literal.
claim_tree=ast.parse((here/'prepare-virtual-up-claim-only.py').read_text())
marker=next(ast.literal_eval(n.value) for n in ast.walk(claim_tree)
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='marker' for t in n.targets))
claim_only=source[:source.index(marker)]+"            return NDIS_STATUS_FAILURE;\n"
assert marker not in claim_only
for variant in [source,claim_only]:
 scoped=api['compose'](variant)
 assert scoped.replace(api['GUARDED'],api['CALL'],1)==variant
patched=api['compose'](source)
assert patched.replace(api['GUARDED'],api['CALL'],1)==source
for bad in [patched,source.replace(api['CALL'],''),source+source,claim_only.replace(api['END'],'')]:
 try:api['compose'](bad)
 except ValueError:pass
 else:raise AssertionError('changed/duplicate source accepted')
guard=api['GUARDED']
c=r'''#include <assert.h>
#include <stdio.h>
#define HIF_MT 1
#define WR_RADIO_BSS_OPEN 2
struct adapter {int mt;struct {int hif_type;} chipCap;
 struct {int BssidNum;struct {struct {void *if_dev;} wdev;} MBSSID[3];} ApCfg;};
#define IS_MT7603(ad) ((ad)->mt)
static int ticks;
static void APUpdateAllBeaconFrame(struct adapter *ad){(void)ad;ticks++;}
static void invoke(struct adapter *pAd,void *device,int operation){
 struct {void *device;int operation;} claim={device,operation};
'''+guard+r'''
}
int main(void){int main_dev,guest,iot;struct adapter ad={.mt=1,.chipCap.hif_type=HIF_MT,.ApCfg.BssidNum=3};
 ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
 invoke(&ad,&iot,WR_RADIO_BSS_OPEN);assert(ticks==0);
 invoke(&ad,&main_dev,WR_RADIO_BSS_OPEN);assert(ticks==1);
 invoke(&ad,&guest,WR_RADIO_BSS_OPEN);assert(ticks==2);
 invoke(&ad,&iot,99);assert(ticks==3);
 ad.mt=0;invoke(&ad,&iot,WR_RADIO_BSS_OPEN);assert(ticks==4);ad.mt=1;
 ad.chipCap.hif_type=0;invoke(&ad,&iot,WR_RADIO_BSS_OPEN);assert(ticks==5);ad.chipCap.hif_type=HIF_MT;
 ad.ApCfg.BssidNum=2;invoke(&ad,&iot,WR_RADIO_BSS_OPEN);assert(ticks==6);
 /* The ordinary periodic caller remains responsible for the next DTIM tick. */
 APUpdateAllBeaconFrame(&ad);assert(ticks==7);
 puts("PASS exact reserved-UP refresh guard: ra2 skips extra global tick; other devices/operations/chips/configs and periodic call preserved. Beacon/MMIO hooks not executed.");}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-reserved-refresh-') as td:
 p=Path(td);(p/'t.c').write_text(c)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
