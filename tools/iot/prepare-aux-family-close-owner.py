#!/usr/bin/env python3
"""Bind non-last APCLI/Monitor family-close ownership in an isolated candidate."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h':'dec42bf8798c4a16d12d4f4e915a06e86650d0a8829bb5218fa2d65d17d5242e',
 'common/rtmp_init.c':'d6f9af5d945371cf7038c5cac8a53ae6ef506d98fd1791630b0cd19c5b5bc7c8',
 'ap/ap_apcli_inf.c':'1c00968c2c0f99238f942d045f74472786bce133980185ae3876d75d11730c36',
 'os/linux/rt_profile.c':'af14d639509bebdcf9d08327bcd5d1da1f6b02a13484bffcf92b21c47934096e',
 'include/wr-iot-virtual-down.inc':'f7fdf857c7886f2517d67346e7ff8fc57efdc5292653aea213ab3da63fe6edf3'}
texts={}
for name,digest in pins.items():
 raw=(src/name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=raw.decode()
def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor '+name)
 texts[name]=texts[name].replace(old,new,1)
one('include/rtmp.h','#include "interface-registry.h"','#include "interface-registry.h"\n#include "aux-family-close.h"')
anchor='struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX + 1];'
one('include/rtmp.h',anchor,anchor+'\n struct wr_iot_family_close wr_iot_family_close[WDEV_NUM_MAX + 1];')
anchor='wr_iot_ref_init(&pAd->wr_iot_interface_refs[wr_iot_slot], NULL, 0);'
one('common/rtmp_init.c',anchor,'{'+anchor+'\n wr_iot_family_close_init(&pAd->wr_iot_family_close[wr_iot_slot]);}')
for name,sig,family,ioctl,command in [
 ('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Close(', 'WR_REF_FAMILY_APCLI','RTMP_AP_IoctlHandle','CMD_RTPRIV_IOCTL_APC_CLOSE'),
 ('os/linux/rt_profile.c','INT Monitor_VirtualIF_Close(', 'WR_REF_FAMILY_MONITOR','RTMP_COM_IoctlHandle','CMD_RTPRIV_IOCTL_SNIFF_CLOSE')]:
 s=texts[name];start=s.index(sig);end=s.index('\n}',start)+2
 callback='wr_iot_'+('apcli' if family.endswith('APCLI') else 'monitor')+'_close_ioctl'
 prefix='#include "wr-iot-aux-family-close-owned.inc"\nstatic INT '+callback+'(RTMP_ADAPTER *ad,PNET_DEV dev){\n return '+ioctl+'(ad,NULL,'+command+',0,dev,0);\n}\n'
 body=s[start:s.index('\n',start)]+'\n{\n if(!dev_p)return -EBUSY;\n return wr_iot_aux_family_close_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,'+family+','+callback+');\n}'
 texts[name]=s[:start]+prefix+body+s[end:]
name='include/wr-iot-virtual-down.inc'
one(name,'pAd->wr_iot_transition.serial != ticket->serial) {',
 'pAd->wr_iot_transition.serial != ticket->serial ||\n     pAd->wr_iot_transition.epoch != ticket->epoch) {')
shutil.copytree(src,out)
for name,s in texts.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(here/'aux-family-close.h',out/'include/aux-family-close.h')
shutil.copyfile(here/'aux-family-close-owned.inc',out/'include/wr-iot-aux-family-close-owned.inc')
print('Bound non-last APCLI/Monitor owned family close; last-close/recovery/callback retirement remain open')
