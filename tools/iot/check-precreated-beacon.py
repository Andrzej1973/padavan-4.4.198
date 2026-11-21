#!/usr/bin/env python3
"""Execute actual candidate beacon predicate for reserved secondary BSS.

Hardware submission, data/probe/auth paths and concurrent teardown are separate.
"""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
fixture_tree=ast.parse((here/'prepare-beacon-guard-check.py').read_text())
values={}
for node in fixture_tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ('prefix','tail'):
    values[target.id]=ast.literal_eval(node.value)
s=(a.candidate/'ap/ap_connect.c').read_text()
start=s.index('BOOLEAN BeaconTransmitRequired(');end=s.index('\n}',start)+2
body=s[start:end]
assert 'RTMP_OS_NETDEV_STATE_RUNNING(pMbss->wdev.if_dev)' in body
body=body.replace('RTMP_ADAPTER *pAd,','RTMP_ADAPTER *pAd __attribute__((unused)),',1)
with tempfile.TemporaryDirectory(prefix='wr-reserved-beacon-') as td:
 c=Path(td)/'check.c';c.write_text(values['prefix']+body+values['tail'])
 for wds in (False,True):
  out=td+('/wds' if wds else '/normal')
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*(['-DWDS_SUPPORT'] if wds else []),str(c),'-o',out],check=True)
  subprocess.run([out],check=True)
print('PASS existing candidate predicate for reserved third BSS: absent/DOWN remains silent despite stale beacon intent; Main/WDS exceptions preserved. No hardware or full lifecycle acceptance.')
