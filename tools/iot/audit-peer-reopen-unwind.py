#!/usr/bin/env python3
"""Assert reopen denial hazards from actual source; no runtime/lifetime proof."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
root=a.candidate.resolve(strict=True)
rel='common/rtmp_init_inf.c';raw=(root/rel).read_bytes();s=raw.decode()
start=s.index('int rt28xx_init(');end=s.index('\nVOID RTMPDrvOpen(',start)
body=s[start:end]
cfg=re.search(r'if\s*\(rtmp_cfg_init\(pAd, pHostName\) != TRUE\)\s*goto err5;',body)
assert cfg
for token in ['hif_sys_init(', 'RtmpNetTaskInit(', 'RtmpMgmtTaskInit(', 'MlmeInit(']:
 assert body.index(token)<cfg.start(),token
tail=body[body.index('err5:'):]
sequence=['err5:','rtmp_cfg_exit(pAd);','err4:','MlmeHalt(pAd);','RTMP_AllTimerListRelease(pAd);','err3:','RtmpMgmtTaskExit(pAd);','err2:','RtmpNetTaskExit(pAd)','err1:','hif_sys_exit(pAd);']
positions=[tail.index(x) for x in sequence];assert positions==sorted(positions)
cfgstart=s.index('INT rtmp_cfg_init(');cfgend=s.index('\n}',cfgstart)+2
assert 'UserCfgInit(pAd);' in s[cfgstart:cfgend]
exitstart=s.index('INT rtmp_cfg_exit(');exitend=s.index('\n}',exitstart)+2
assert 'UserCfgExit(pAd);' in s[exitstart:exitend]
init=(root/'common/rtmp_init.c').read_text()
initstart=init.index('VOID UserCfgInit(')
# Delimit by the next top-level routine, not a column-zero nested closing brace.
initend=init.index('\nUCHAR BtoH(',initstart)
initbody=init[initstart:initend]
assert 'NdisZeroMemory(&pAd->MacTab, sizeof(MAC_TABLE));' in initbody
assert not re.search(r'\breturn\s*;',initbody)
outer=(root/'os/linux/rt_main_dev.c').read_text()
ostart=outer.index('int rt28xx_open(VOID *dev)');oend=outer.index('\n}',ostart)+2
openbody=outer[ostart:oend]
for token in ['DiagProcInit(pAd);','RTMP_DRIVER_MCU_SLEEP_CLEAR(pAd);','load_dev_l1profile(pAd)','RtmpOSIRQRequest(net_dev);','RTMP_DRIVER_IRQ_INIT(pAd);']:
 assert openbody.index(token)<openbody.index('if (rt28xx_init('),token
assert 'RTMP_DRIVER_IRQ_RELEASE(pAd);' in openbody[openbody.index('err:'):]
ap=(root/'ap/ap.c').read_text();astart=ap.index('VOID APStartUp(')
apbody=ap[astart:ap.index('\nBOOLEAN APStop(',astart)]
assert 'AsicUpdateWdsRxWCIDTable(pAd);' in apbody
assert body.index('rtmp_cfg_init(')<body.index('APStartUp(pAd);')<body.index('return TRUE;')
wds=(root/'ap/ap_wds.c').read_text()
wstart=wds.index('VOID AsicUpdateWdsRxWCIDTable(');wend=wds.index('\nVOID AsicUpdateWdsEncryption(',wstart)
assert 'wr_iot_wds_insert_transaction(pAd, wds_entry->PeerWdsAddr, index, 2)' in wds[wstart:wend]
assert 'MacTableInsertEntry(pAd, pAddr, wdev, ENTRY_WDS, OPMODE_AP, TRUE)' in wds
r={'scope':'source assertions for initialization ordering and destructive error unwind',
 'source_sha256':{rel:hashlib.sha256(raw).hexdigest(),'common/rtmp_init.c':hashlib.sha256((root/'common/rtmp_init.c').read_bytes()).hexdigest()},
 'passed':True,'cfg_failure_unwind':sequence,
 'mutations_before_cfg':['hif_sys_init','RtmpNetTaskInit','RtmpMgmtTaskInit','MlmeInit'],
 'finding':'denying only UserCfgInit/rtmp_cfg_init is too late: caller tears down retained adapter resources through err5',
 'outer_open_mutations_before_init':['DiagProcInit','MCU sleep clear','profile load','IRQ request','IRQ init'],
 'outer_failure_cleanup':'rt28xx_open releases IRQ on rt28xx_init FALSE',
 'startup_insertion_chain':['rt28xx_init','APStartUp','AsicUpdateWdsRxWCIDTable','wr_iot_wds_insert_transaction','MacTableInsertEntry'],
 'startup_reservation_hazard':'blanket insertion denial held through complete init would reject configured WDS startup peers',
 'required_binding':['reserve before rt28xx_open first side effect, not merely inner rt28xx_init','admission refusal returns directly without entering initialization or IRQ unwind','carry exact serial through config clear, then explicitly hand off to startup admission before APStartUp','startup owner must distinguish authorized insertions from unrelated mutation; no global owner bypass','retain on partial failure; do not release into automatic reuse','audit timer task startup, full clears, shutdown and adapter free against same owner'],
 'parser_note':'UserCfgInit contains nested column-zero closing brace; first newline brace is not a reliable full-function boundary',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False}
a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print('PASS source ordering: config refusal enters destructive unwind after four initialization subsystems')
