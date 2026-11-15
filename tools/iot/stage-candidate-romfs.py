#!/usr/bin/env python3
"""Stage a verified pair into a new isolated ROMFS; never modify the baseline."""
import argparse,hashlib,json,os,runpy,shutil,stat
from pathlib import Path
here=Path(__file__).resolve().parent
pair_build=runpy.run_path(str(here/'package-candidate-pair.py'))['build']
def snapshot(root):
 records={}
 for directory,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:
   p=Path(directory)/name;n=p.relative_to(root).as_posix();s=p.lstat()
   item={'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISLNK(s.st_mode):item.update(type='link',target=os.readlink(p))
   elif stat.S_ISDIR(s.st_mode):item.update(type='directory')
   elif stat.S_ISREG(s.st_mode):item.update(type='file',sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())
   else:raise ValueError('Unsupported ROMFS entry '+n)
   records[n]=item
 return records

def stage(baseline,results,manifest,revision,kernel_config,output):
 baseline=baseline.resolve();results=results.resolve()
 if output.exists() or output.is_symlink():raise ValueError('Output must not exist')
 destination=output.resolve()
 for source in (baseline,results):
  if destination.is_relative_to(source) or source.is_relative_to(destination):raise ValueError('Output overlaps inputs')
 expected=pair_build(results,revision)
 if manifest!=expected:raise ValueError('Pair manifest/source mismatch')
 candidate_config=(results/'ra2-no-host-module/kernel.config').read_bytes()
 if kernel_config.is_symlink() or kernel_config.read_bytes()!=candidate_config:
  raise ValueError('Baseline and candidate kernel configs differ; coherent kernel build required')
 before=snapshot(baseline)
 modules=[n for n,r in before.items() if n.startswith('lib/modules/') and n.endswith('/mt76x3_ap.ko')]
 if len(modules)!=1 or before[modules[0]]['type']!='file':raise ValueError('Require one regular baseline MT7603 module')
 replacements={modules[0] if n=='driver:mt76x3_ap' else n:r for n,r in expected['files'].items()}
 for name in replacements:
  if name not in before or before[name]['type']!='file':raise ValueError('Missing/aliased baseline target '+name)
  parent=Path(name).parent
  while parent!=Path('.'):
   if before.get(parent.as_posix(),{}).get('type')!='directory':raise ValueError('Symlink/non-directory target parent '+str(parent))
   parent=parent.parent
 # A replacement must not affect another baseline hardlink destination.
 identities={}
 for n,r in before.items():
  if r['type']=='file':
   s=(baseline/n).stat();identities.setdefault((s.st_dev,s.st_ino),[]).append(n)
 for names in identities.values():
  if len(names)>1 and any(n in replacements for n in names):raise ValueError('Aliased baseline replacement '+str(names))
 shutil.copytree(baseline,output,symlinks=True,copy_function=shutil.copy2)
 for name,record in replacements.items():
  source=results/record['source'];data=source.read_bytes()
  if source.is_symlink() or hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Payload changed '+name)
  (output/name).write_bytes(data)
 after=snapshot(output)
 if before.keys()!=after.keys():raise ValueError('Unexpected ROMFS entries')
 for name in before:
  if name in replacements:
   if after[name]['sha256']!=replacements[name]['sha256'] or before[name]['mode']!=after[name]['mode']:
    raise ValueError('Replacement/mode mismatch '+name)
  elif before[name]!=after[name]:raise ValueError('Unrelated ROMFS content changed '+name)
 if before!=snapshot(baseline):raise ValueError('Baseline changed during staging')
 return {'board':'WR1200JS','source_revision':revision,'module_destination':modules[0],
         'replacement_sha256':{n:r['sha256'] for n,r in replacements.items()},
         'unrelated_entries_preserved':len(before)-len(replacements),
         'baseline_unchanged':True,'isolated_romfs_staged':True,'dependency_closure_at_image_paths_verified':False,
         'trx_built':False,'production_installed':False,'physical_runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('results',type=Path)
 p.add_argument('--manifest',type=Path,required=True);p.add_argument('--revision',required=True)
 p.add_argument('--kernel-config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.report.exists():raise SystemExit('Report already exists')
 r=stage(a.baseline,a.results,json.loads(a.manifest.read_text()),a.revision,a.kernel_config,a.output)
 a.report.write_text(json.dumps(r,indent=2)+'\n')
 print('PASS isolated ROMFS payload identities and unrelated content preservation; image build/dependencies/device remain separate')
