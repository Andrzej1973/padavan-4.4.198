#!/usr/bin/env python3
"""Expose direct exact-ticket retry after unmutated auxiliary DOWN failure."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/wr-iot-aux-family-close-owned.inc':'d2f77700cc37c565003bb230eae372fc19417a4f3b68da1f333336a431d3e78e',
 'ap/ap_apcli_inf.c':'7c9b35a2a5b589eaf28d11afc33ea56dfc4c0a3efdc761f7e620719a9cdd715c',
 'os/linux/rt_profile.c':'5745b6727b8a1573e70a505b1df90bca5fe9a1b6b2fa41cd46c4b23f88452972',
 'include/rtmp.h':'dc1a202fa5f71438077c736d9d85e36ae75ba949a99cb413a5629dec0de4b55b'}
texts={}
for name,digest in pins.items():
 raw=(src/name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=raw.decode()
texts['include/wr-iot-aux-family-close-owned.inc']+='\n'+(here/'aux-family-close-retry.inc').read_text()
for name,fn,family in [('ap/ap_apcli_inf.c','ApCli_VirtualIF_Close','WR_REF_FAMILY_APCLI'),
 ('os/linux/rt_profile.c','Monitor_VirtualIF_Close','WR_REF_FAMILY_MONITOR')]:
 s=texts[name];start=s.index('INT '+fn+'(');end=s.index('\n}',start)+2
 wrapper='\n/* Caller pins device/adapter and holds RTNL; no automatic retry scheduler. */\nINT '+fn+'_Retry(PNET_DEV dev_p)\n{\n if(!dev_p)return -EBUSY;\n return wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,'+family+');\n}\n'
 texts[name]=s[:end]+wrapper+s[end:]
anchor='INT wr_iot_netdev_close_phase_idle(RTMP_ADAPTER *pAd, PNET_DEV dev);'
if texts['include/rtmp.h'].count(anchor)!=1:p.error('changed prototype anchor')
texts['include/rtmp.h']=texts['include/rtmp.h'].replace(anchor,anchor+'\nINT ApCli_VirtualIF_Close_Retry(PNET_DEV dev_p);\nINT Monitor_VirtualIF_Close_Retry(PNET_DEV dev_p);',1)
shutil.copytree(src,out)
for name,s in texts.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
print('Bound direct same-ticket auxiliary DOWN retry; scheduler/retained lifetime integration remains open')
