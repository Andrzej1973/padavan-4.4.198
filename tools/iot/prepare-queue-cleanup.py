#!/usr/bin/env python3
"""Stage pinned dispatch/shutdown cleanup hooks; no producer or radio operation."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:
    raise SystemExit('Output must be new and separate')
blobs={'common/rtmp_init.c':'a0d9eb2adbbb2ac13e8314806a5ded2f30793623',
       'os/linux/rt_rbus_pci_drv.c':'07f1171dc14081af70ba6a1537bf896a9b141be3'}
originals={};texts={}
for name,blob in blobs.items():
    data=(root/name).read_bytes()
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blob:
        raise SystemExit('Unreviewed cleanup source: '+name)
    originals[name]=data;texts[name]=data.decode('utf-8')
def patch_function(text,signature,anchor,replacement):
    if text.count(signature)!=1:raise SystemExit('Changed function signature')
    start=text.index(signature);end=text.index('\n}',start)+2
    function=text[start:end]
    if function.count(anchor)!=1:raise SystemExit('Changed cleanup anchor')
    return text[:start]+function.replace(anchor,replacement,1)+text[end:]
name='common/rtmp_init.c'
anchor='\t\tif (cmdqelmt->CmdFromNdis == TRUE)'
texts[name]=patch_function(texts[name],'VOID CMDHandler(RTMP_ADAPTER *pAd)',anchor,
 '\t\twr_iot_queue_cleanup(cmdqelmt);\n'+anchor)
anchor='\t\t\tswitch (cmdqelmt->command)'
texts[name]=patch_function(texts[name],'VOID CMDHandler(RTMP_ADAPTER *pAd)',anchor,
 '\t\t\t/* No radio binding: checked work returns failure. */\n'
 '\t\t\tif (!wr_iot_queue_dispatch(pAd, cmdqelmt, NULL)) {\n'+anchor)
anchor='\t\t\t}\n\t\t}\n\n\t\twr_iot_queue_cleanup(cmdqelmt);'
texts[name]=patch_function(texts[name],'VOID CMDHandler(RTMP_ADAPTER *pAd)',anchor,
 '\t\t\t}\n\t\t\t}\n\t\t}\n\n\t\twr_iot_queue_cleanup(cmdqelmt);')
name='os/linux/rt_rbus_pci_drv.c'
anchor='\t\t\t\tif (pCmdQElmt->CmdFromNdis == TRUE)'
texts[name]=patch_function(texts[name],'INT RTPCICmdThread(',anchor,
 '\t\t\t\twr_iot_queue_cleanup(pCmdQElmt);\n'+anchor)
for name,text in texts.items():
    # Keep hook declarations after the driver types supplied by rt_config.
    lines=text.splitlines(keepends=True)
    hits=[i for i,line in enumerate(lines) if line.lstrip().startswith('#include') and '"rt_config.h"' in line]
    if len(hits)!=1:raise SystemExit('Changed driver include')
    header='queued-work.h' if name=='common/rtmp_init.c' else 'queued-cleanup.h'
    lines.insert(hits[0]+1,'#include "'+header+'"\n')
    texts[name]=''.join(lines)
for name,data in originals.items():
    if (root/name).read_bytes()!=data:raise SystemExit('Source changed')
out.mkdir()
for name,text in texts.items():
    target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
for name in ('queued-result.h','queued-cleanup.h','queued-work.h'):
    target=out/'include'/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(Path(__file__).with_name(name).read_bytes())
(out/'manifest.json').write_text(json.dumps({'source_blobs':blobs,
 'production_installed':False,'producer_bound':False,'worker_dispatch_staged':True,
 'radio_operation_bound':False,
 'target_compiled':False,'shutdown_concurrency_verified':False},indent=2)+'\n')
print('Prepared isolated dispatch/shutdown cancellation hooks; no producer/radio binding')
