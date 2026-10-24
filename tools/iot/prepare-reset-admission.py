#!/usr/bin/env python3
"""Stage pinned top-level PSE/PDMA admission; not installed in production."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:raise SystemExit('New separate output required')
name='common/cmm_mac_pci.c';data=(root/name).read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='82db49fa1822a51268d76f23bce94d886f4d50d6':raise SystemExit('Unreviewed reset source')
s=data.decode()
for public,raw in [('PDMAResetAndRecovery','wr_iot_pdma_reset_raw'),('PSEResetAndRecovery','wr_iot_pse_reset_raw')]:
 old='VOID '+public+'(RTMP_ADAPTER *pAd)'
 if s.count(old)!=1:raise SystemExit('Changed reset definition')
 s=s.replace(old,'static VOID '+raw+'(RTMP_ADAPTER *pAd)',1)
start=s.index('static VOID wr_iot_pse_reset_raw(');end=s.index('\n}',start)+2
f=s[start:end]
if f.count('PDMAResetAndRecovery(pAd);')!=1:raise SystemExit('Changed nested PDMA call')
f=f.replace('PDMAResetAndRecovery(pAd);','wr_iot_pdma_reset_raw(pAd);',1)
s=s[:start]+f+'\n#include "wr-iot-reset-admission.inc"\n'+s[end:]
if (root/name).read_bytes()!=data:raise SystemExit('Source changed')
out.mkdir();(out/'common').mkdir();(out/'include').mkdir()
(out/name).write_text(s,encoding='utf-8')
(out/'include/wr-iot-reset-admission.inc').write_bytes(Path(__file__).with_name('reset-admission.inc').read_bytes())
(out/'manifest.json').write_text(json.dumps({'production_installed':False,'top_level_reset_wrappers_staged':True,
 'periodic_retry_bound':False,'retirement_proven':False,'target_compiled':False},indent=2)+'\n')
print('Prepared top-level reset admission; nested PSE/PDMA shares one ticket; production/lifetime pending')
