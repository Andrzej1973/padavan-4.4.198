#!/usr/bin/env python3
"""Phase 1A read-only call-site inventory; not a shell execution/dependency graph."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def inventory():
 workflow='.github/workflows/build-padavan-4.4-wr1200js.yml'
 lines=(ROOT/workflow).read_text().splitlines();calls=[];step='';inline=[]
 dirty=set(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines())
 for number,line in enumerate(lines,1):
  match=re.match(r'\s+- (?:name|id):\s*(.*)',line)
  if match:step=match.group(1)
  if re.search(r'\bpython3\s+-\s*(?:<<|$)',line):inline.append({'line':number,'step':step})
  for match in re.finditer(r'\b(python3|node|bash|sh)\s+([A-Za-z0-9_./-]+\.(?:py|sh|js))\b',line):
   command,path=match.groups();p=ROOT/path;exists=p.is_file()
   calls.append({'line':number,'step':step,'interpreter':command,'path':path,'worktree_file_exists':exists,'worktree_modified':path in dirty,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if exists else None})
 return {'phase':'1A initial inventory','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'workflow':workflow,'workflow_sha256':hashlib.sha256((ROOT/workflow).read_bytes()).hexdigest(),'calls':calls,'inline_python_blocks':inline,'unique_paths':len({v['path'] for v in calls}),'scope':'Static textual call sites in workflow line order. Conditions, working-directory changes, shell variables, inline code and subprocess calls require manual tracing; this is not a complete execution graph. Dirty tool hashes describe this worktree, not prior CI.','source_moves':[]}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args();report=inventory();args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'calls':len(report['calls']),'unique_paths':report['unique_paths'],'inline_blocks':len(report['inline_python_blocks']),'report':str(args.output)}))
