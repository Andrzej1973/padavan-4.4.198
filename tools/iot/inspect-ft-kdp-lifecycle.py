#!/usr/bin/env python3
"""Inventory pinned KDP control-block users before composing AP teardown."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
path=a.source/'ap/ap_ftkd.c';source=path.read_text(encoding='latin1')
# Keep offsets stable while masking comments and string/character literals.
masked=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
 lambda m:' '*len(m[0]),source,flags=re.S)
functions=[]
pattern=r'\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{'
for match in re.finditer(pattern,masked):
 name=match[1]
 if name in ('if','for','while','switch'):continue
 start=match.end()-1;end=start+1;depth=1
 while depth and end<len(masked):
  depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
 if depth:raise ValueError('unbalanced function '+name)
 functions.append((name,match.start(),end))
users=[];covered=set()
for name,start,end in functions:
 accesses=[]
 for m in re.finditer(r'\b(?:FT_KDP_CB|pFT_KDP_Ctrl_BK|FlgIsFtKdpInit|FT_KdpLock)\b',masked[start:end]):
  offset=start+m.start();covered.add(offset)
  accesses.append({'symbol':m[0],'line':source.count('\n',0,offset)+1})
 if accesses:users.append({'function':name,'line':source.count('\n',0,start)+1,'accesses':accesses})
all_offsets={m.start() for m in re.finditer(r'\b(?:FT_KDP_CB|pFT_KDP_Ctrl_BK|FlgIsFtKdpInit|FT_KdpLock)\b',masked)}
assert covered==all_offsets,'unclassified KDP state access'
by_name={name:source[start:end] for name,start,end in functions}
release=by_name['FT_KDP_Release']
assert release.index('pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK = NULL;')<release.index('RTMPCancelTimer(&FT_KDP_CB->TimerReport')
assert 'FT_KDP_EventInform' in by_name and 'FT_KDP_InfoBroadcast' in by_name
header=(a.source/'include/ft_cmm.h').read_text(encoding='latin1')
assert '/*#define FT_KDP_FUNC_INFO_BROADCAST' in header
receipt={
 'scope':'source inventory; not runtime concurrency or effective target macro evidence',
 'sha256':{'ap/ap_ftkd.c':hashlib.sha256(path.read_bytes()).hexdigest(),
           'include/ft_cmm.h':hashlib.sha256((a.source/'include/ft_cmm.h').read_bytes()).hexdigest()},
 'control_block_users':users,
 'unclassified_accesses':len(all_offsets-covered),
 'constraints':[
  'Cache API leases do not cover all KDP entry points; KDP release needs whole-operation lifetime admission before control block and FT_KdpLock release',
  'Native FT_KDP_Init is void and may return on control block allocation failure; the caller must not assume successful KDP initialization',
  'Native FT_KDP_Init ignores OS_ABL FT_KdpLock allocation return; FlgIsFtKdpInit alone is insufficient evidence of valid allocated lock',
  'APStop and APStopBssOnly already mutate AP state before late FT_Release call; FT drain reservation must precede first AP side effects and failure must reach callers',
  'Under FT_KDP_FUNC_INFO_BROADCAST native release sets control block NULL before evaluating its TimerReport member for cancel',
  'Broadcast define is commented out in pinned header; effective target command-line definitions remain unverified',
  'Timer cancel/release task-queue quiescence and all control-block users must be verified before native KDP free'
 ],
 'next_required':'Bind KDP whole-operation users and a pre-side-effect AP release reservation; then compose KDP/RIC/cache release under that reservation and verify FT_R1KH_KEEP transitions',
 'producer_installed':False,'target_compiled':False,'runtime_verified':False}
# Calls are lexical potential edges across all feature branches. Do not treat
# this inventory as effective preprocessor or runtime reachability evidence.
names={name for name,_,_ in functions if name.startswith('FT_')}
edges=[]
for name,start,end in functions:
    body_start=masked.index('{',start)+1
    for match in re.finditer(r'\b(FT_[A-Za-z0-9_]+)\s*\(',masked[body_start:end]):
        if match[1] in names:
            offset=body_start+match.start()
            edges.append({'caller':name,'callee':match[1],
                          'line':source.count('\n',0,offset)+1})
assert any(e['caller']=='FT_KDP_R0KH_InfoAdd' and e['callee']=='FT_KDP_R0KH_InfoDel' for e in edges)
assert any(e['caller']=='FT_KDP_KeyRequestToUs' and e['callee']=='FT_KDP_EventInform' for e in edges)
receipt['internal_potential_call_edges']=edges
receipt['admission_constraint']='Outer admitted calls must invoke internal implementations using their existing lease; independently re-admitting nested calls after close may partially execute the outer operation. No global or per-adapter bypass flag may substitute for exact caller ownership.'
receipt['callgraph_limitations']='Lexical direct FT calls in ap_ftkd.c only; macros, indirect callbacks, other translation units and effective feature selection require separate inventory.'
a.output.write_text(json.dumps(receipt,indent=2)+'\n')
print('PASS | FT KDP lifecycle inventory | '+str(len(users))+' functions; all control-block/init/lock accesses classified; cache-only drain insufficient')
