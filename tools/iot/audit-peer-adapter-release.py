#!/usr/bin/env python3
"""Record actual adapter release call sites and ABI barriers; lexical audit only."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.candidate.resolve(strict=True)
if a.output.exists():p.error('new report output required')
report={'candidate':str(root),'scope':'lexical source/ABI audit, not control-flow or lifetime proof',
 'target_compiled':False,'runtime_verified':False,'release_accepted':False,'files':{},'call_sites':[]}
for f in sorted(root.rglob('*.c')):
 # Vendor comments use mixed encodings. Latin1 preserves every byte; only
 # ASCII C identifiers are searched, without lossy replacement or omission.
 s=f.read_bytes().decode('latin1');sites=[]
 for m in re.finditer(r'(?m)^\s*(RTMPFreeAdapter|RtmpRaDevCtrlExit)\s*\(\s*pAd\s*\)\s*;',s):
  before=s[max(0,m.start()-180):m.start()];after=s[m.end():m.end()+240]
  sites.append({'path':f.relative_to(root).as_posix(),'line':s[:m.start()].count('\n')+1,
    'callee':m.group(1),'result_checked':False,'before':before.strip(),'after':after.strip()})
 if sites:
  report['files'][f.relative_to(root).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
  report['call_sites'].extend(sites)
header=root/'include/rt_os_net.h';h=header.read_text()
profile=root/'os/linux/rt_profile.c';s=profile.read_text()
report['free_abi']={'native_void':bool(re.search(r'VOID RTMPFreeAdapter\(VOID \*pAd\);',h)),
 'ops_void':bool(re.search(r'VOID \(\*RTMPFreeAdapter\)\(VOID \*pAd\);',h)),
 'implementation_void':'VOID RTMPFreeAdapter(VOID *pAdSrc)' in s,
 'mactab_lock_free_line':s[:s.index('NdisFreeSpinLock(&pAd->MacTabLock);')].count('\n')+1}
init=root/'common/rtmp_init.c';s=init.read_text();start=s.index('BOOLEAN RtmpRaDevCtrlExit(');end=s.index('\n}',start)+2
body=s[start:end]
destructors=[name for name in ['RTMP_SEM_EVENT_DESTORY','os_free_mem','RTMPFreeTxRxRingMemory']
  if name in body and body.index(name)<body.index('RTMPFreeAdapter(pAd)')]
claims=[body.find(name) for name in ['wr_iot_pci_retirement_claim_release(','wr_iot_adapter_release_begin(']]
first_destructor=min((body.index(name) for name in destructors),default=len(body))
report['controller_exit']={'free_result_propagated':'if (!RTMPFreeAdapter(pAd)) return FALSE;' in body,
 'destructors_before_adapter_free':[name for name in ['RTMP_SEM_EVENT_DESTORY','os_free_mem','RTMPFreeTxRxRingMemory']
  if name in body and body.index(name)<body.index('RTMPFreeAdapter(pAd)')],
 'release_claim_before_destructors':any(0<=position<first_destructor for position in claims)}
for f in [header,profile,init]:report['files'][f.relative_to(root).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
report['required_next_actions']=[
 'Claim retirement before the first controller destructor, not only inside RTMPFreeAdapter.',
 'Propagate refusal through native/OS_ABL and every caller before unmapping CSR or freeing cookies.',
 'Handle cold probe unwind separately from initialized adapter shutdown.',
 'Prove final work, callback, timer, peer, registry and DMA retirement; then atomically forbid new owners.']
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
abi='VOID' if report['free_abi']['ops_void'] else 'non-VOID (review target ABI)'
print('OPEN: '+str(len(report['call_sites']))+' unchecked direct release calls; '+abi+' free ABI; no release acceptance')
