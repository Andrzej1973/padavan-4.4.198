#!/usr/bin/env python3
"""Stage checked MLME task halt before destructive shutdown cleanup."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text())
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or actual!=m['merged_driver_sha256'] or 'pci_netdev_preclose_layer' not in m:p.error('changed or unsupported merged input')
s=(src/'common/mlme.c').read_text();start=s.index('VOID MlmeHalt(RTMP_ADAPTER *pAd)');end=s.index('\n}',start)+2;original=s[start:end]
if hashlib.sha256(original.encode()).hexdigest()!='caf50808ecf4a058dd37c96888c0ef1a925ee2033039b895f05f3260fd0e6990':p.error('unreviewed MLME halt')
body=original.replace('VOID MlmeHalt(RTMP_ADAPTER *pAd)','static BOOLEAN wr_iot_mlme_halt_body(RTMP_ADAPTER *pAd, BOOLEAN checked)',1)
old='\t\tDBGPRINT(RT_DEBUG_ERROR, ("kill mlme task failed!\\n"));'
assert body.count(old)==1;body=body.replace(old,old+'\n        if (checked) return FALSE;',1)
body=body[:-2]+'\n return TRUE;\n}'
wrappers='''
/* Preserve the legacy entry while checked shutdown propagates join failure. */
VOID MlmeHalt(RTMP_ADAPTER *pAd)
{
 (void)wr_iot_mlme_halt_body(pAd, FALSE);
}
BOOLEAN wr_iot_mlme_halt_checked(RTMP_ADAPTER *pAd)
{
 /* OS identity helper accepts any RTMP_OS_TASK; unknown/self must refuse. */
 if (!pAd || wr_iot_os_join_context() ||
     wr_iot_os_timer_task_current(&pAd->mlmeTask) != 0) return FALSE;
 return wr_iot_mlme_halt_body(pAd, TRUE);
}
'''
changed={'common/mlme.c':s[:start]+body+wrappers+s[end:]}
s=(src/'include/rtmp.h').read_text();old='VOID MlmeHalt(RTMP_ADAPTER *pAd);';assert s.count(old)==1
changed['include/rtmp.h']=s.replace(old,old+'\nBOOLEAN wr_iot_mlme_halt_checked(RTMP_ADAPTER *pAd);',1)
s=(src/'common/rtmp_init_inf.c').read_text();start=s.index('static INT wr_iot_checked_close_body(');end=s.index('\nINT wr_iot_',start+1) if '\nINT wr_iot_' in s[start+1:] else len(s)
# Only the checked shutdown occurrence; legacy/init-failure calls stay intact.
pos=s.index('\tMlmeHalt(pAd);',start)
assert pos<end
old='\tMlmeHalt(pAd);'
new=''' if (!wr_iot_mlme_halt_checked(pAd)) {
  /* Stage-zero cleanup already mutated state: retain; never replay it. */
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  pAd->wr_iot_transition.shutdown_stage=3U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }'''
changed['common/rtmp_init_inf.c']=s[:pos]+new+s[pos+len(old):]
# Prove each full source transformation is reversible before writing output.
assert changed['common/mlme.c'].replace(body+wrappers,original,1)==(src/'common/mlme.c').read_text()
assert changed['include/rtmp.h'].replace('BOOLEAN wr_iot_mlme_halt_checked(RTMP_ADAPTER *pAd);\n','',1)==(src/'include/rtmp.h').read_text()
assert changed['common/rtmp_init_inf.c'].replace(new,old,1)==s
shutil.copytree(src,out)
for rel,text in changed.items():
 (out/rel).write_text(text);digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mlme_checked_halt_layer']={'target_compiled':False,'runtime_verified':False,'timer_retirement_proven':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged checked MLME halt; timer/reader retirement remains separate')
