#!/usr/bin/env python3
"""Prepare a source overlay for separate data tasklet join; close is unbound."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def prepare(files):
    result = dict(files)
    def one(name, old, new):
        if result[name].count(old) != 1:
            raise ValueError('Changed data-lane anchor: '+name+': '+old)
        result[name] = result[name].replace(old, new)
    header = 'include/rtmp.h'; init = 'common/rtmp_init.c'
    sched = 'include/wr-iot-nettask-schedule.inc'; net = 'os/linux/rt_rbus_pci_drv.c'
    one(header, '#include "tasklet-schedule-owner.h"',
        '#include "tasklet-schedule-owner.h"\n#include "nettask-lane-owner.h"')
    one(header, 'struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner;',
        'struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner;\n'
        ' struct wr_iot_tasklet_schedule_owner wr_iot_nettask_data_owner;\n'
        ' unsigned int wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;')
    one(header, 'INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);',
        'INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);\nINT wr_iot_nettask_data_exit(RTMP_ADAPTER *pAd);')
    one(init, 'wr_iot_tasklet_schedule_init(&pAd->wr_iot_nettask_owner);',
        'wr_iot_tasklet_schedule_init(&pAd->wr_iot_nettask_owner);\n'
        ' wr_iot_tasklet_schedule_init(&pAd->wr_iot_nettask_data_owner);\n'
        ' pAd->wr_iot_nettask_data_joined=1;pAd->wr_iot_nettask_data_joining=0;')
    if 'RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,' not in result[sched]:
        raise ValueError('Expected current IRQ-save nettask locking')
    one(sched, ' ULONG flags = 0;int entered;', ' ULONG flags = 0;int entered,mcu_lane;')
    one(sched, ' if(!pAd||!task)return;',
        ' if(!pAd||!task)return;\n mcu_lane=wr_iot_nettask_is_mcu(pAd,task);')
    one(sched, 'entered=wr_iot_tasklet_schedule_enter(&pAd->wr_iot_nettask_owner);',
        'entered=wr_iot_nettask_lane_enter(&pAd->wr_iot_nettask_owner,\n'
        '               &pAd->wr_iot_nettask_data_owner,mcu_lane);')
    one(sched, '(void)wr_iot_tasklet_schedule_leave(&pAd->wr_iot_nettask_owner);',
        '(void)wr_iot_nettask_lane_leave(&pAd->wr_iot_nettask_owner,\n'
        '               &pAd->wr_iot_nettask_data_owner,mcu_lane);')
    one(sched, 'ready=wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner);',
        'ready=wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner)&&\n'
        '       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);')
    one(sched, 'if(pAd->wr_iot_nettask_initializing){',
        'if(pAd->wr_iot_nettask_initializing||pAd->wr_iot_nettask_data_joining){')
    one(sched, 'wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_owner);',
        'wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_owner);\n'
        ' wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_data_owner);')
    one(sched, 'accepted=!pAd->wr_iot_nettask_release_claimed',
        'accepted=pAd->wr_iot_nettask_data_joined&&\n'
        '  wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner)&&\n'
        '  !pAd->wr_iot_nettask_release_claimed')
    one(sched, 'if(accepted){pAd->wr_iot_nettask_joined=0;',
        'if(accepted){\n'
        ' accepted=wr_iot_tasklet_schedule_open(&pAd->wr_iot_nettask_data_owner,1,1);\n'
        ' if(!accepted){wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_owner);\n'
        '  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return NDIS_STATUS_FAILURE;}\n'
        ' pAd->wr_iot_nettask_data_joined=0;pAd->wr_iot_nettask_joined=0;')
    one(sched, 'ready=!pAd->wr_iot_nettask_release_claimed',
        'ready=pAd->wr_iot_nettask_data_joined&&!pAd->wr_iot_nettask_data_joining&&\n'
        ' wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner)&&\n'
        ' !pAd->wr_iot_nettask_release_claimed')
    result[sched] = '#include "wr-iot-nettask-data-drain.inc"\n'+result[sched]
    source = result[net]; start = source.index('INT RtmpNetTaskExit(')
    end = source.index('\n}', start)+2; body = source[start:end]
    data = body.replace('INT RtmpNetTaskExit(', 'INT wr_iot_nettask_data_exit(', 1)
    data = data.replace('wr_iot_nettask_block_drain(pAd)', 'wr_iot_nettask_data_block_drain(pAd)', 1)
    data = data.replace('wr_iot_nettask_joined', 'wr_iot_nettask_data_joined')
    for name in ('rx1_done_task','hcca_dma_done_task'):
        old = '\tRTMP_OS_TASKLET_KILL(&pObj->'+name+');'
        if data.count(old) != 1: raise ValueError('Changed MCU task inventory: '+name)
        data = data.replace(old, '')
    data = data.replace('pAd->wr_iot_nettask_data_joined=1;',
                        'pAd->wr_iot_nettask_data_joined=1;pAd->wr_iot_nettask_data_joining=0;', 1)
    declarations=re.findall(r' ULONG wr_flags(?: = 0)?;int wr_joined;',data)
    if len(declarations)!=1:raise ValueError('Changed exit declarations')
    anchor = declarations[0]
    if data.count(anchor) != 1: raise ValueError('Changed cookie binding')
    data = data.replace(anchor, anchor + '\n'
        '#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)\n'
        ' if(!IS_MT7603(pAd)||pAd->chipCap.hif_type!=HIF_MT)return NDIS_STATUS_FAILURE;\n'
        '#else\n return NDIS_STATUS_FAILURE;\n#endif', 1)
    body = body.replace('pAd->wr_iot_nettask_joined=1;',
                        'pAd->wr_iot_nettask_joined=1;pAd->wr_iot_nettask_data_joined=1;', 1)
    result[net] = source[:start]+body+'\n\n'+data+source[end:]
    here = Path(__file__).resolve().parent
    for name, local in (('include/nettask-lane-owner.h','nettask-lane-owner.h'),
                        ('include/wr-iot-nettask-data-drain.inc','nettask-data-drain.inc')):
        result[name] = (here/local).read_text()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a = p.parse_args(); src = a.source.resolve(); out = a.output.resolve()
    if out.exists() or src==out or src in out.parents or out in src.parents:
        p.error('Expected separate new overlay directory')
    names = ('include/rtmp.h','common/rtmp_init.c',
             'include/wr-iot-nettask-schedule.inc','os/linux/rt_rbus_pci_drv.c')
    changes = prepare({name:(src/name).read_text() for name in names})
    out.mkdir(parents=True)
    for name,text in changes.items():
        path = out/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    (out/'overlay.json').write_text(json.dumps({
        'scope':'data-lane overlay only; physical close not bound',
        'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changes},
        'target_compiled':False,'runtime_verified':False},indent=2)+'\n')


if __name__=='__main__':main()
