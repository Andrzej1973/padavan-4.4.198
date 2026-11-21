#!/usr/bin/env python3
"""Stable CI entry point; shared catalogue validation lives in repository module."""
import json,os,sys
from pathlib import Path
from repository.board_catalog import load,select

try:selected=select(load(Path.cwd()),sys.argv[1] if len(sys.argv)>1 else 'all-supported')
except (ValueError,KeyError) as error:raise SystemExit(str(error))
value=json.dumps({'include':[{'board':b['id']} for b in selected]},separators=(',',':'))
print(value)
if os.environ.get('GITHUB_OUTPUT'):
 with open(os.environ['GITHUB_OUTPUT'],'a') as output:output.write('matrix='+value+'\n')
Path('selected-boards.json').write_text(json.dumps(selected,indent=2)+'\n')
