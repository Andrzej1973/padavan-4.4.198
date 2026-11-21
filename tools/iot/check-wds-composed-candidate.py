#!/usr/bin/env python3
"""Run WDS ownership regressions against one composed candidate's headers."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
p.add_argument('--cc',default='gcc')
a=p.parse_args();src=a.candidate.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate results directory required')
out.mkdir(parents=True);here=Path(__file__).resolve().parent
specs=[
 ('peer-operation','check-wds-peer-operation.c',[]),
 ('retirement-identity','check-wds-retirement-identity.c',[]),
 ('ageout','check-wds-ageout-transaction.c',[]),
 ('retirement-close','check-wds-retirement-close-gate.c',[]),
 ('registry','check-interface-registry.c',[]),
 ('aux-close','check-aux-close-claim.c',[]),
 ('delete-identity','check-wds-peer-delete-gate.c',[]),
 ('hardware-observer','check-wds-hardware-delete-observer.c',[]),
 ('hardware-both','check-wds-hardware-delete-result.c',['-DMT_MAC','-DWDS_SUPPORT']),
 ('hardware-mt','check-wds-hardware-delete-result.c',['-DMT_MAC']),
 ('hardware-wds','check-wds-hardware-delete-result.c',['-DWDS_SUPPORT']),
 ('hardware-neither','check-wds-hardware-delete-result.c',[]),
]
if (src/'include/wr-iot-wds-ageout-recovery.inc').exists():
 specs.append(('ageout-recovery','check-wds-ageout-transaction.c',['-DTEST_WDS_RECOVERY']))
if (src/'include/timer-task-owner.h').exists():
 specs.append(('timer-task-owner','check-timer-task-owner.c',[]))
if (src/'include/wr-iot-timer-checked-join.inc').exists():
 specs.extend([('timer-join-direct','check-timer-checked-join.c',[]),
               ('timer-join-task','check-timer-checked-join.c',['-DRTMP_TIMER_TASK_SUPPORT'])])
 for abl in (False,True):
  for thread in (False,True):
   specs.append(('timer-os-join-'+str(abl)+'-'+str(thread),'check-timer-os-join.c',
     (['-DOS_ABL_FUNC_SUPPORT'] if abl else [])+(['-DKTHREAD_SUPPORT'] if thread else [])))
if (src/'include/wr-iot-peer-hardware-insert-result.inc').exists():
 timer_flags=['-DTEST_TIMER_FENCE'] if (src/'include/wr-iot-peer-failed-timer-fence.inc').exists() else []
 specs.extend([('peer-insert-mt','check-peer-hardware-insert-result.c',['-DMT_MAC',*timer_flags]),
               ('peer-insert-legacy','check-peer-hardware-insert-result.c',[])])
 if timer_flags:
  specs.append(('peer-timer-features','check-peer-hardware-insert-result.c',[
   '-DMT_MAC',*timer_flags,'-DCONFIG_AP_SUPPORT','-DAPCLI_SUPPORT','-DDOT11W_PMF_SUPPORT',
   '-DAPCLI_DOT11W_PMF_SUPPORT','-DWSC_INCLUDED']))
report={'passed':False,'target_compiled':False,'runtime_verified':False,
 'lifecycle_accepted':False,'scope':'sequential host tests with injected vendor/kernel operations',
 'tests':[],'candidate':str(src),
 'headers':{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted((src/'include').glob('*')) if q.is_file()}}
try:
 for name,test,flags in specs:
  fixture=out/(name+'.c');exe=out/(name+'.exe')
  text=(here/test).read_text().replace('"wds-peer-delete-gate.inc"','"wr-iot-wds-peer-delete-gate.inc"')
  fixture.write_text(text,encoding='utf-8',newline='\n')
  subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(src/'include'),*flags,str(fixture),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
  report['tests'].append({'name':name,'flags':flags,'passed':True,
   'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest()})
 report['passed']=True
finally:
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS '+str(len(report['tests']))+' composed WDS host variants; target/runtime unverified')
