#!/usr/bin/env python3
"""Compare exact owner-preparer pinned inputs with a supplied driver tree."""
import argparse,ast,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
results=[]
for name in ('prepare-peer-table-owner.py','prepare-peer-close-executor.py'):
 script=here/name;tree=ast.parse(script.read_text());pins=None
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pins' for t in node.targets):
   pins=ast.literal_eval(node.value);break
 if not isinstance(pins,dict):raise ValueError('literal pin map missing '+name)
 rows=[]
 for relative,expected in pins.items():
  path=a.source/relative
  actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
  rows.append({'path':relative,'expected':expected,'actual':actual,'matches':actual==expected})
 results.append({'preparer':name,'preparer_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
                 'all_inputs_match':all(r['matches'] for r in rows),'inputs':rows})
a.output.write_text(json.dumps({'scope':'exact source input identity only; does not execute preparers or validate ownership','predecessors':results,
 'required_next':'Reproduce the existing staged candidate chain with exact pin receipts before replacing association-owner stand-in; do not weaken hash gates or call field-only schema complete integration',
 'target_compiled':False,'producer_installed':False},indent=2)+'\n')
for result in results:
 print(('PASS' if result['all_inputs_match'] else 'FAIL')+' | owner predecessor identity | '+result['preparer']+' | '+str(sum(r['matches'] for r in result['inputs']))+'/'+str(len(result['inputs']))+' pinned inputs match')
# Audit success is distinct from predecessor acceptance.
print('SUMMARY | owner predecessor audit completed; mismatches forbid preparer application')
