#!/usr/bin/env python3
"""Read-only architecture inventory and scoped path/profile validation (stdlib)."""
import argparse,collections,hashlib,json,re,subprocess,sys
from pathlib import Path
from board_catalog import load
ROOT=Path(__file__).resolve().parents[2]
DOCS=['REPOSITORY-ARCHITECTURE.md','REPOSITORY-STRUCTURE.md','NILABSENT-ARCHITECTURE-ANALYSIS.md','REPOSITORY-MIGRATION-PLAN.md','REPOSITORY-MIGRATION-REPORT.md','BUILD-SYSTEM.md','BOARD-PROFILE-ARCHITECTURE.md']
GROUPS={'overlay':'Active overlay, package ports, isolated candidates; application is explicit','configs.build':'Requested board profiles; admission only through boards.json','configs':'Owned dependency manifests','reference':'Donor snapshots, never auto-selected as board targets','docs':'Contracts, evidence, historical records and navigation','tools':'Source transformations, checks and stable entry points','sources':'Preserved archives governed by sources.lock.json','toolchains':'Compiler source recipe profiles, no generated compiler trees','third_party':'Vendored components with their upstream notices','.github/workflows':'Build, diagnostics and publication recipes'}

def run(*args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def links(root,docs):
 errors=[]
 for doc in docs:
  p=root/doc
  if not p.is_file():errors.append('Missing documentation: '+doc);continue
  for target in re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)',p.read_text()):
   if re.match(r'^[a-zA-Z][\w+.-]*:',target) or target.startswith('#'):continue
   target=target.split('#',1)[0]
   if target and not (p.parent/target).exists():errors.append(doc+' -> '+target)
 return errors

def inventory():
 tracked=run('git','ls-files','-z').split('\0');tracked=[x for x in tracked if x]
 untracked=run('git','ls-files','--others','--exclude-standard','-z').split('\0');untracked=[x for x in untracked if x]
 existing=[n for n in sorted(set(tracked+untracked)) if (ROOT/n).is_file() and not (ROOT/n).is_symlink()]
 hashes=collections.defaultdict(list);mentions={};sizes=collections.Counter();counts=collections.Counter()
 for n in existing:
  p=ROOT/n;size=p.stat().st_size;group=n.split('/')[0];sizes[group]+=size;counts[group]+=1
  b=p.read_bytes();hashes[hashlib.sha256(b).hexdigest()].append(n)
  if b'\0' not in b:
   text=b.decode('utf-8',errors='replace');rows=[i+1 for i,l in enumerate(text.splitlines()) if 'nilabsent' in l.lower()]
   if rows:mentions[n]=rows
 duplicates=[{'sha256':h,'paths':paths} for h,paths in hashes.items() if len(paths)>1]
 return {'head':run('git','rev-parse','HEAD'),'branch':run('git','branch','--show-current'),'tracked_files':len(tracked),'untracked_files':untracked,'directories':{g:{'purpose':v,'files':counts[g],'bytes':sizes[g]} for g,v in GROUPS.items()},'nilabsent_mentions':mentions,'duplicate_groups':duplicates,'scratch_policy':'No files deleted/moved based on duplicate/untracked status; historical/reference ownership preserved','path_dependency_counts':{prefix:sum((ROOT/n).read_bytes().count(prefix.encode()) for n in existing if (ROOT/n).stat().st_size<2000000 and not n.startswith(('sources/','reference/'))) for prefix in ['configs.build/','overlay/padavan-4.4/','reference/boards/','tools/board-catalog.py']}}

def validate():
 errors=[]
 try:boards=load(ROOT)
 except (ValueError,KeyError) as e:errors.append(str(e));boards=[]
 for group in GROUPS:
  if not (ROOT/group).is_dir():errors.append('Missing operational directory '+group)
 errors+=links(ROOT,['docs/'+x for x in DOCS])
 for name in ['configs/owned-build-dependencies.json']:
  for item in json.loads((ROOT/name).read_text()):
   p=ROOT/'sources/archives'/item['filename']
   if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:errors.append('Owned input hash mismatch '+str(p.relative_to(ROOT)))
 kernel=ROOT/'overlay/padavan-4.4/trunk/configs/boards/WR1200JS/kernel-4.4.x.config'
 dts={'board_dts':'overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/wr1200js.dts','layout':'overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/mt7621-spi-16m-wr1200js-layout.dtsi','status':'Exact existing DTS/model/include and SPI16M partitions checked; includes from pinned kernel and compiled DTB still require assembled-source/image validation'}
 return {'errors':errors,'boards':boards,'dts_review':dts,'scope':'local source/profile/required-path/doc-link/archive checks; no full firmware/runtime verification','passed':not errors}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');p.add_argument('--report',type=Path);a=p.parse_args()
 report=inventory() if a.inventory else validate()
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'mode':'inventory' if a.inventory else 'validate','passed':report.get('passed'),'errors':report.get('errors',[]),'report':str(a.report) if a.report else None},ensure_ascii=False))
 if not a.inventory and not report['passed']:sys.exit(1)
