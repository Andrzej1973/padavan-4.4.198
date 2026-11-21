#!/usr/bin/env python3
"""Inspect actual staged AP result paths before binding FT reservations."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
path=a.source/'ap/ap.c';text=path.read_text(encoding='latin1');rows=[]
for name,reset in [('APStop','MacTableReset'),('APStopBssOnly','MacTableResetWdev')]:
 signature='BOOLEAN '+name+'('
 assert text.count(signature)==1
 start=text.index(signature);end=text.index('\n}',start)+2;body=text[start:end]
 assert body.count('FT_Release(pAd);')==1
 assert body.index('RTMP_ASIC_INTERRUPT_DISABLE(pAd);')<body.index(reset+'(')<body.index('FT_Release(pAd);')
 returns=[{'line':text.count('\n',0,start+m.start())+1,'statement':m[0]} for m in re.finditer(r'return\s+(?:FALSE|TRUE)\s*;',body)]
 rows.append({'function':name,'line':text.count('\n',0,start)+1,'returns':returns,'reset_before_ft_release':True})
callers=[]
for file in sorted(a.source.rglob('*.c')):
 content=file.read_text(encoding='latin1')
 for line,statement in enumerate(content.splitlines(),1):
  if re.search(r'\bAPStop(?:BssOnly)?\s*\(',statement) and not re.match(r'\s*BOOLEAN\s+APStop',statement):
   callers.append({'path':str(file.relative_to(a.source)),'line':line,'statement':statement.strip()})
executor=a.source/'include/peer-close-executor.h'
assert executor.is_file()
executor_text=executor.read_text()
assert 'unsigned int lane,running,retained;unsigned long serial;' in executor_text
assert callers
a.output.write_text(json.dumps({'scope':'actual reproduced peer-retirement AP source; no mutation/execution','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'functions':rows,'direct_stop_callers':callers,'close_executor_sha256':hashlib.sha256(executor.read_bytes()).hexdigest(),'carrier_assessment':'Existing executor stores lane/serial only, with no BSS identity or FT ticket; direct APStop callers include config/radar/WSC paths outside RTMPDrvClose, so close executor alone is not sufficient AP ownership','constraints':['AP interrupt disable precedes fallible MacTableReset/ResetWdev; these are already partial-stop paths','A local-only FT ticket reserved at entry is lost on reset FALSE and cannot be reacquired while cache is DESTROYING','Reservation must be stored in an adapter-owned AP operation with exact operation/BSS identity and resume state, or rolled back only when absence of side effects is proved','Retry must reuse original ticket and skip completed teardown phases; a fresh local ticket or cold-success shortcut is insufficient','FT_R1KH_KEEP requires retained-cache and releasing-cache operations to have distinct outcomes','All KDP entrants/release must share lifetime before installing this reservation'],'next_required':'Bind durable AP operation identity/resume before redirecting FT_Release; inspect existing close executor ownership as the carrier','producer_installed':False,'target_compiled':False},indent=2)+'\n')
print('PASS | staged AP reservation audit | both BOOLEAN stop paths, fallible reset after side effects, durable ticket/resume requirement recorded')
