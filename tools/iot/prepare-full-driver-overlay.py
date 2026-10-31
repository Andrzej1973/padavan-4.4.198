#!/usr/bin/env python3
"""Prepare a new full-driver scratch overlay; never install or build it."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('candidate',type=Path)
p.add_argument('composition',type=Path,help='Reviewed pre-producer composition manifest')
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.source.resolve(strict=True); candidate=a.candidate.resolve(strict=True); out=a.output.resolve()
if out.exists() or any(x==out or x in out.parents or out in x.parents for x in (source,candidate)):
    p.error('output must be new and separate')
def files(tree):
    result={}
    for f in tree.rglob('*'):
        if f.is_symlink():
            p.error('symlink input refused: '+str(f))
        if f.is_file():result[f.relative_to(tree).as_posix()]=f.read_bytes()
    return result
def digest(data):return hashlib.sha256(data).hexdigest()
base=files(source); changes=files(candidate)
manifest=json.loads(a.composition.read_text(encoding='utf-8'))
receipt=json.loads(candidate.with_name(candidate.name+'-generation.json').read_text())
if manifest.get('source_revision')!='c25283e915a2a00a763774dd255b14aff997285e' or manifest.get('production_installed') is not False:
    p.error('unreviewed composition provenance')
if {n:digest(b) for n,b in changes.items()}!=receipt['candidate_sha256']:
    p.error('candidate differs from generation receipt')
for name,expected in manifest['source_git_blobs'].items():
    if name not in base:p.error('missing original source: '+name)
    b=base[name]
    if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=expected:
        p.error('original source blob differs: '+name)
rows=manifest['files']; names={r['path'] for r in rows}
extra={'include/wr-iot-beacon-producer-gate.h','include/wr-iot-beacon-producer-kernel.h'}
if len(names)!=len(rows) or set(changes)!=names|extra:
    p.error('candidate inventory differs from reviewed producer composition')
fixtures={r['path'] for r in rows if r.get('purpose')=='fixture' and '/' not in r['path']}
# Include fragments under include/ are consumed by driver translation units,
# even when older manifests label their generator stage as a fixture.
if any(n in base for n in fixtures):p.error('fixture collides with original driver')
# Validate every path before writing anything.
for name in set(base)|set(changes):
    q=Path(name)
    if q.is_absolute() or '..' in q.parts:p.error('unsafe relative path')
merged=dict(base)
merged.update({n:b for n,b in changes.items() if n not in fixtures})
include_checks=0
for name,data in merged.items():
    if Path(name).suffix not in ('.c','.h','.inc'):continue
    for inc in re.findall(r'^\s*#\s*include\s*"([^"]+)"',data.decode('latin1'),re.M):
        if not inc.startswith('wr-iot-'):continue
        include_checks+=1
        choices=[(Path(name).parent/inc).as_posix(), 'include/'+inc, 'mcu/'+inc]
        if not any(n in merged for n in choices):
            p.error('missing candidate include '+inc+' from '+name)
shutil.copytree(source,out)
for name,data in changes.items():
    if name in fixtures:continue
    dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
actual=files(out); expected=dict(base)
expected.update({n:b for n,b in changes.items() if n not in fixtures})
if actual!=expected:raise SystemExit('overlay content verification failed')
report={'source_revision':manifest['source_revision'],
 'candidate_include_references_checked':include_checks,
 'verified_original_blob_count':len(manifest['source_git_blobs']),
 'base_sha256':{n:digest(b) for n,b in base.items()},
 'overlay_sha256':{n:digest(b) for n,b in actual.items()},
 'excluded_fixtures':sorted(fixtures),'candidate_files_applied':len(changes)-len(fixtures),
 'full_upstream_inventory_authenticated':False,
 'target_compiled':False,'production_installed':False,'runtime_verified':False}
out.with_name(out.name+'-overlay.json').write_text(json.dumps(report,indent=2)+'\n')
merge_manifest={'schema':1, 'source_revision':manifest['source_revision'],
 'source_git_blobs':manifest['source_git_blobs'],
 'files':[{'path':n,'sha256':digest(b)} for n,b in sorted(changes.items()) if n not in fixtures],
 'target_compiled':False,'production_installed':False,'runtime_verified':False,
 'scope':'candidate input for prepared-source merge; merge itself not performed'}
out.with_name(out.name+'-merge-input.json').write_text(json.dumps(merge_manifest,indent=2)+'\n')
print('PASS full scratch overlay verified; no target compile or installation')
