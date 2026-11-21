#!/usr/bin/env python3
"""Fence periodic/IOCTL actors against bootstrap; other remap users remain open."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_boot_scheduler_quota' not in m or 'mcu_control_admission' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated quota candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed control admission anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_scheduler_state;',
 'unsigned int wr_iot_boot_scheduler_state;\n unsigned int wr_iot_control_users,wr_iot_control_poisoned;')
one('common/rtmp_init.c','pAd->wr_iot_boot_scheduler_state=0;',
 'pAd->wr_iot_boot_scheduler_state=0;\n        pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;')
one('include/wr-iot-mcu-boot-transport.inc',
 'ready=!ad->wr_iot_boot_active && !ad->wr_iot_boot_failed &&',
 'ready=!ad->wr_iot_control_users && !ad->wr_iot_control_poisoned &&\n       !ad->wr_iot_boot_active && !ad->wr_iot_boot_failed &&')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-transport.inc"',
 '#include "wr-iot-mcu-control-admission.inc"\n#include "wr-iot-mcu-boot-transport.inc"')
anchor='INT32 wr_iot_mcu_boot_reserve(struct _RTMP_ADAPTER *ad,unsigned long peer_serial,struct wr_iot_mcu_boot_ticket *out);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_control_enter(struct _RTMP_ADAPTER *ad);\nVOID wr_iot_control_leave(struct _RTMP_ADAPTER *ad);')
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
for name,signature,rawname,wrapper in (
 ('common/mlme.c','NTSTATUS MlmePeriodicExec(IN PRTMP_ADAPTER pAd, IN PCmdQElmt CMDQelmt)',
  'wr_iot_mlme_periodic_raw', '''NTSTATUS MlmePeriodicExec(IN PRTMP_ADAPTER pAd, IN PCmdQElmt CMDQelmt)
{
 NTSTATUS status;
GUARD
 if(IS_MT7603(pAd)&&!wr_iot_control_enter(pAd))return NDIS_STATUS_SUCCESS;
#endif
 status=wr_iot_mlme_periodic_raw(pAd,CMDQelmt);
GUARD
 if(IS_MT7603(pAd))wr_iot_control_leave(pAd);
#endif
 return status;
}
'''),
 ('os/linux/rt_main_dev.c','INT rt28xx_ioctl(PNET_DEV net_dev, struct ifreq *rq, INT cmd)',
  'wr_iot_linux_ioctl_raw', '''INT rt28xx_ioctl(PNET_DEV net_dev, struct ifreq *rq, INT cmd)
{
 INT status;
GUARD
 RTMP_ADAPTER *ad=NULL;
 GET_PAD_FROM_NET_DEV(ad,net_dev);
 if(!ad)return -ENETDOWN;
 if(IS_MT7603(ad)&&!wr_iot_control_enter(ad))return -EBUSY;
#endif
 status=wr_iot_linux_ioctl_raw(net_dev,rq,cmd);
GUARD
 if(IS_MT7603(ad))wr_iot_control_leave(ad);
#endif
 return status;
}
''')):
 # Add a private forward declaration and public wrapper immediately before body.
 public=signature.split('(')[0].split()[-1]
 private='static '+signature.replace(public+'(',rawname+'(',1)
 one(name,signature+'\n{',private+';\n'+wrapper.replace('GUARD',guard)+'\n'+private+'\n{')
changes['include/wr-iot-mcu-control-admission.inc']=Path(__file__).with_name('mcu-control-admission.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_control_admission']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'covered_actors':['linux_ioctl','mlme_periodic'],
 'all_remap_users_covered':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
