#!/usr/bin/env python3
"""Bind internal open-owner ioctl transport only; outer open/WDS unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp_cmd.h':'dd0b3954778d33fe1addd20796f8d036fdae11da8849338f114e59a308c52a54',
 'include/rtmp.h':'bc224c5db96333c59778bcec3b1b258d85cdd78db7fb4464f64dee385aa53d39',
 'common/rtmp_init.c':'668f930a94303f009dc0152d6c7b71cd26b9980b4a5c78c54b0774d166a5bef8',
 'common/cmm_cfg.c':'45de3f1a54d428bb0f92125c7fe63c06eaf7e0f97310609ba3e3b5c9f27980bd'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
# Append after existing enum: preserve all old command and sentinel values.
texts['include/rtmp_cmd.h']=one(texts['include/rtmp_cmd.h'],'} CMD_RTPRIV_IOCTL_COMMON;',
 '} CMD_RTPRIV_IOCTL_COMMON;\n#define CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER 0x7f20\n#include "peer-open-request.h"')
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'#include "peer-table-owner.h"',
 '#include "peer-table-owner.h"\n#include "peer-open-owner.h"')
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;\n struct wr_iot_peer_open_owner wr_iot_peer_open_owner;')
texts['common/rtmp_init.c']=one(texts['common/rtmp_init.c'],
 'wr_iot_peer_table_owner_init(&pAd->wr_iot_peer_table_owner);',
 'wr_iot_peer_table_owner_init(&pAd->wr_iot_peer_table_owner);\n\t\twr_iot_peer_open_owner_init(&pAd->wr_iot_peer_open_owner);')
s=texts['common/cmm_cfg.c'];s=one(s,'INT RTMP_COM_IoctlHandle(',
 '#include "wr-iot-peer-open-dispatch.inc"\n\nINT RTMP_COM_IoctlHandle(')
s=one(s,'\t\tcase CMD_RTPRIV_IOCTL_NETDEV_GET:',
 '''\t\tcase CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER:
   if (wrq || subcmd) return NDIS_STATUS_FAILURE;
   return wr_iot_peer_open_dispatch(pAd,(struct wr_iot_peer_open_request *)pData,Data);
\t\tcase CMD_RTPRIV_IOCTL_NETDEV_GET:''')
texts['common/cmm_cfg.c']=s
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
for local,target in [('peer-open-owner.h','peer-open-owner.h'),('peer-open-request.h','peer-open-request.h'),('peer-open-dispatch.inc','wr-iot-peer-open-dispatch.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-peer-open-transport.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'internal dispatch transport only, outer open and WDS call binding absent',
 'old_command_values_preserved':True,'outer_open_bound':False,'wds_startup_bound':False,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged internal open ticket transport; outer caller/WDS not bound')
