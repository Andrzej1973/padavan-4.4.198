#!/usr/bin/env python3
"""Wrap both close bodies with one adapter-owned software executor."""
import argparse,hashlib,shutil,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'common/rtmp_init_inf.c':'58df1c881e4f1d37f1178fbe5646b08c01c189541c71664b99e2126493319899',
 'common/rtmp_init.c':'353637d8fdfee6355d2e727be1addab1e75e4f48e0fe2b75beb1e14eda472abb',
 'include/rtmp.h':'5960c192632c0a8ee3d06b746511c2a9c3ed3b48a0f2e22339f262c200acf54b',
 'include/wr-iot-peer-open-dispatch.inc':'65c59733e514a763c92506715c914e61148f9a6ba5f52d4668f3c5ca802f21c7'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('changed anchor: '+old)
 return s.replace(old,new,1)
name='include/rtmp.h'
texts[name]=one(texts[name],'#include "peer-table-owner.h"',
 '#include "peer-table-owner.h"\n#include "peer-close-executor.h"')
texts[name]=one(texts[name],'unsigned int wr_iot_peer_legacy_close_state;',
 'unsigned int wr_iot_peer_legacy_close_state;\n struct wr_iot_peer_close_executor wr_iot_peer_close_executor;')
name='common/rtmp_init.c'
texts[name]=one(texts[name],'pAd->wr_iot_peer_legacy_close_state=0;',
 'pAd->wr_iot_peer_legacy_close_state=0;\n\t\twr_iot_peer_close_executor_init(&pAd->wr_iot_peer_close_executor);')
name='common/rtmp_init_inf.c';s=texts[name]
s=one(s,'INT RTMPDrvClose(', 'static INT wr_iot_legacy_close_body(')
s=one(s,'INT wr_iot_drv_close_checked(VOID *pAdSrc, VOID *net_dev,\n const struct wr_iot_radio_ticket *ticket)',
 'static INT wr_iot_checked_close_body(VOID *pAdSrc, VOID *net_dev,\n const struct wr_iot_radio_ticket *ticket,int *wr_started)')
start=s.index('static INT wr_iot_checked_close_body(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'if (stage == 2U) return NDIS_STATUS_SUCCESS;',
 'if (stage == 2U) return NDIS_STATUS_SUCCESS;\n *wr_started=1;')
s=s[:start]+body+'\n#include "wr-iot-peer-close-executor.inc"'+s[end:];texts[name]=s
name='include/wr-iot-peer-open-dispatch.inc'
texts[name]=one(texts[name],'if (request->serial || pAd->MacTab.Size || pAd->wr_iot_peer_legacy_close_state==1U) break;',
 'if (request->serial || pAd->MacTab.Size || pAd->wr_iot_peer_legacy_close_state==1U ||\n      !wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor)) break;')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
for name,target in [('peer-close-executor.h','peer-close-executor.h'),('peer-close-executor.inc','wr-iot-peer-close-executor.inc')]:
 shutil.copyfile(Path(__file__).with_name(name),out/'include'/target)
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':pins,
 'scope':'both synchronous close bodies and main-open dispatch exclusion',
 'target_compiled':False,'runtime_verified':False,'adapter_release_bound':False,
 'all_radio_reset_paths_serialized':False},indent=2)+'\n')
print('Staged shared close executor; all-radio and adapter-free retirement still unproved')
