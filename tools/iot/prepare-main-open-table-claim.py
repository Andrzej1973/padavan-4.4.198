#!/usr/bin/env python3
"""Bind early main open/config reservation; shutdown/full-clear release unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rt_os_net.h':'8e16cae1117e32840bce7856b3e213f8574fdf813d3fb8efd47c8e61c25805f0',
 'os/linux/rt_main_dev.c':'ca3efffe5f4a07bff1e6dc8263a1955be264de67d4333a3c5661da8cb6d97382',
 'common/rtmp_init_inf.c':'e4c1357fede7dc933d52c8cd41f50365c7fffed28b2c0d45e656ddd51b4868ef'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['include/rt_os_net.h']
s=one(s,'#include "radio-transition.h"','#include "radio-transition.h"\n#include "peer-open-request.h"')
for old in ['int (*rt28xx_init)(VOID *pAd,  RTMP_STRING *pDefaultMac, RTMP_STRING *pHostName);',
            'int rt28xx_init(VOID *pAd, RTMP_STRING *pDefaultMac, RTMP_STRING *pHostName);']:
 s=one(s,old,old.replace('pHostName);','pHostName, const struct wr_iot_peer_open_request *wr_claim);'))
texts['include/rt_os_net.h']=s
s=texts['os/linux/rt_main_dev.c'];start=s.index('int rt28xx_open(VOID *dev)');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'\tULONG OpMode;', '\tULONG OpMode;\n struct wr_iot_peer_open_request wr_claim={WR_IOT_PEER_OPEN_REQUEST_VERSION,WR_PEER_OPEN_BEGIN,net_dev,0};')
body=one(body,'#ifdef WIFI_DIAG',
 '''/* Refusal before diagnostics/profile/IRQ changes must not enter err unwind. */
 if(wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_BEGIN)!=NDIS_STATUS_SUCCESS)return -EBUSY;
#ifdef WIFI_DIAG''')
body=one(body,'rt28xx_init(pAd, mac, hostname)', 'rt28xx_init(pAd, mac, hostname,&wr_claim)')
body=one(body,'err:\n', 'err:\n (void)wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_FAIL);\n')
s=s[:start]+'#include "wr-iot-peer-open-client.inc"\n'+body+s[end:];texts['os/linux/rt_main_dev.c']=s
s=texts['common/rtmp_init_inf.c'];start=s.index('int rt28xx_init(');end=s.index('\nVOID RTMPDrvOpen(',start);body=s[start:end]
body=one(body,'RTMP_STRING *pHostName)', 'RTMP_STRING *pHostName,const struct wr_iot_peer_open_request *wr_claim)')
body=one(body,'\tNDIS_STATUS Status;', '\tNDIS_STATUS Status;\n struct wr_iot_peer_open_request wr_request;\n int wr_config_released=0;')
body=one(body,'\tif (!pAd)\n\t\treturn FALSE;',
 '''\tif (!pAd || !wr_claim) return FALSE;
 wr_request=*wr_claim;
 if(wr_iot_peer_open_call(pAd,&wr_request,WR_PEER_OPEN_CONFIG_CHECK)!=NDIS_STATUS_SUCCESS)return FALSE;''')
body=one(body,'\t\tAPStartUp(pAd);',
 '''  if(wr_iot_peer_open_release_config(pAd,&wr_request)!=NDIS_STATUS_SUCCESS)goto err8;
  wr_config_released=1;
\t\tAPStartUp(pAd);''')
body=one(body,'\tDBGPRINT_S(("<==== rt28xx_init, Status=%x\\n", Status));',
 ''' if(!wr_config_released && wr_iot_peer_open_release_config(pAd,&wr_request)!=NDIS_STATUS_SUCCESS)goto err8;
\tDBGPRINT_S(("<==== rt28xx_init, Status=%x\\n", Status));''')
s=s[:start]+'#include "wr-iot-peer-open-client.inc"\n'+body+s[end:];texts['common/rtmp_init_inf.c']=s
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
for n,target in [('peer-open-client.inc','wr-iot-peer-open-client.inc'),('peer-open-request.h','peer-open-request.h'),('peer-open-dispatch.inc','wr-iot-peer-open-dispatch.inc')]:
 shutil.copyfile(Path(__file__).with_name(n),out/'include'/target)
out.with_name(out.name+'-main-open-table-claim.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'early outer open and inner config reservation; no final radio readiness proof',
 'rt28xx_init_abi_changed':True,'coherent_target_module_rebuild_required':True,
 'shutdown_full_clear_owner_bound':False,'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged early main open table claim and explicit core init ticket')
