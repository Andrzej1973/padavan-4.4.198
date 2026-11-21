#!/usr/bin/env python3
"""Inventory actual tasklet schedule sites; no runtime or effective-config proof."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.candidate.resolve(strict=True)
if a.output.exists():p.error('new report output required')
def blank(match):return ''.join('\n' if c=='\n' else ' ' for c in match.group())
report={'candidate':str(root),'scope':'lexical C scheduling inventory; conditional branches all included',
 'files':{},'sites':[],'scheduling_fence_bound':False,'runtime_verified':False}
for f in sorted(root.rglob('*.c')):
 raw=f.read_bytes();source=raw.decode('latin1')
 code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',blank,source,flags=re.S)
 matches=list(re.finditer(r'\b(RTMP_OS_TASKLET_SCHE|tasklet_hi_schedule|tasklet_schedule|schedule_work|schedule_delayed_work)\s*\(',code))
 if not matches:continue
 name=f.relative_to(root).as_posix();report['files'][name]=hashlib.sha256(raw).hexdigest()
 for match in matches:
  line=code[:match.start()].count('\n')+1
  report['sites'].append({'path':name,'line':line,'api':match.group(1),'source':source.splitlines()[line-1].strip()})
report['count']=len(report['sites'])
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Tasklet schedule inventory: '+str(report['count'])+' sites in '+str(len(report['files']))+' files; no fence acceptance')
