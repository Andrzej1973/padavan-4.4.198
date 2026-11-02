#!/usr/bin/env python3
"""Stage init-failure RX join before MCU controller cleanup; isolated only."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
parent=json.loads(src.with_name(src.name+'.manifest.json').read_text())
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=parent['merged_driver_sha256'] or parent.get('production_installed') is not False:p.error('changed merged input')
name='common/rtmp_init_inf.c';s=(src/name).read_text()
if hashlib.sha256((src/name).read_bytes()).hexdigest()!='e778d450b0346db8f56dc13dd4ec7b954efc4303b87ba088a6bafc5ae0a1affd':p.error('unreviewed init source')
old='err6:\n\tMCUSysExit(pAd);'
new='''err6:
 /* Match MCUSysExit firmware stop, then retire/join physical RX before
  * controller queues and locks disappear. Later err2 join is idempotent.
  * A refused join must retain controller resources for recovery. */
 if (pAd->chipOps.FwExit) pAd->chipOps.FwExit(pAd);
 if (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) return FALSE;
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 if (!wr_iot_mcu_dma_disabled_idle(pAd)) return FALSE;
#endif
 MCU_CTRL_EXIT(pAd);'''
assert s.count(old)==1
changed=s.replace(old,new);assert changed.replace(new,old)==s
anchor='#include\t"rt_config.h"'
assert changed.count(anchor)==1
changed=changed.replace(anchor,anchor+'\n#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-dma-disabled-idle.inc"\n#endif',1)
shutil.copytree(src,out);(out/name).write_text(changed)
shutil.copyfile(Path(__file__).with_name('mcu-dma-disabled-idle.inc'),out/'include/wr-iot-mcu-dma-disabled-idle.inc')
helper='include/wr-iot-mcu-dma-disabled-idle.inc'
parent['merged_driver_sha256'][helper]=hashlib.sha256((out/helper).read_bytes()).hexdigest()
parent['candidate_driver_sha256'][helper]=parent['merged_driver_sha256'][helper]
parent['merged_driver_sha256'][name]=hashlib.sha256((out/name).read_bytes()).hexdigest()
parent['candidate_driver_sha256'][name]=parent['merged_driver_sha256'][name]
parent['mcu_init_rx_join_layer']={'production_installed':False,'target_compiled':False,'runtime_verified':False,'scope':'init failure FwExit then checked RX join then MCU cleanup; IRQ/DMA terminal proof separate'}
parent.update(production_installed=False,target_compiled=False,runtime_verified=False)
out.with_name(out.name+'.manifest.json').write_text(json.dumps(parent,indent=2)+'\n')
print('Staged init-failure RX join before MCU cleanup; hardware quiescence unproved')
