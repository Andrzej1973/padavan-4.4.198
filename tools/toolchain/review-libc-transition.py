#!/usr/bin/env python3
"""Review only the pinned uClibc 1.0.43 -> 1.0.48 image transition."""
import argparse,hashlib,importlib.util,json,re,subprocess,tempfile,zipfile
from pathlib import Path

PAIRS={f'lib/{name}-1.0.43.so':f'lib/{name}-1.0.48.so' for name in ['ld-uClibc','libthread_db','libuClibc']}
spec=importlib.util.spec_from_file_location('image_closure',Path(__file__).resolve().parents[1]/'band-steering/verify-package-closure.py')
closure=importlib.util.module_from_spec(spec);spec.loader.exec_module(closure)

def exports(path):
 text=subprocess.check_output(['readelf','--dyn-syms','--wide',str(path)],text=True)
 return {p[7] for line in text.splitlines() if len(p:=line.split())>=8 and p[4] in ['GLOBAL','WEAK'] and p[5] in ['DEFAULT','PROTECTED'] and p[6]!='UND'}

def verify_root(root,report):
 errors=[];resolved={}
 actual={}
 for path in root.rglob('*'):
  if path.is_symlink() or not path.is_file():continue
  with path.open('rb') as stream:magic=stream.read(4)
  if magic==b'\x7fELF':actual[path.relative_to(root).as_posix()]=path
 if set(actual)!=set(report['elf_files']):raise ValueError('Image/report ELF inventory mismatch')
 for name,item in report['elf_files'].items():
  if hashlib.sha256(actual[name].read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Image/report ELF digest mismatch: '+name)
  for dep in item['abi']['needed']:
   if '/' in dep:raise ValueError('Unreviewed dependency path: '+dep)
   target=None
   for folder in ['lib','usr/lib']:
    try:target=closure.resolve_image(root,folder+'/'+dep);break
    except ValueError as error:
     if not str(error).startswith('Missing image file:'):raise
   if target is None:errors.append(name+' -> '+dep)
   else:resolved[dep]=target.relative_to(root).as_posix()
  for loader in item['abi']['interpreter']:
   try:resolved[loader]=closure.resolve_image(root,loader).relative_to(root).as_posix()
   except ValueError:errors.append(name+' -> '+loader)
 if errors:raise ValueError('Unresolved image dependencies: '+str(errors))
 return {'elf_count':len(actual),'resolved':resolved,'errors':errors}

def unpack(archive,report,destination):
 if len(report['images'])!=1:raise ValueError('Expected exactly one WR1200JS image')
 filename,expected=next(iter(report['images'].items()))
 if Path(archive).is_dir():
  names=list(Path(archive).rglob(filename))
  if len(names)!=1:raise ValueError('Ambiguous image directory')
  data=names[0].read_bytes()
 else:
  with zipfile.ZipFile(archive) as z:
   names=[n for n in z.namelist() if n.endswith('/'+filename) or n==filename]
   if len(names)!=1:raise ValueError('Ambiguous image archive')
   data=z.read(names[0])
 if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('Image archive digest mismatch')
 image=destination/'image.trx';image.write_bytes(data)
 offset=data.find(b'hsqs')
 if offset<0:raise ValueError('Missing SquashFS magic')
 root=destination/'root'
 subprocess.run(['unsquashfs','-no-progress','-processors','1','-offset',str(offset),'-dest',str(root),str(image)],check=True,stdout=subprocess.DEVNULL)
 return root

def review(a,b,aroot,broot):
 if a['source_sha']!=b['source_sha'] or (a['variant'],b['variant'])!=('pinned','source'):raise ValueError('Unmatched source/lanes')
 roots={'control':verify_root(aroot,a),'source':verify_root(broot,b)}
 pairs=[]
 for old,new in PAIRS.items():
  av,bv=a['elf_files'][old],b['elf_files'][new]
  if av['abi']!=bv['abi']:raise ValueError('Renamed library ABI drift: '+new)
  sonames=[]
  for root,name in [(aroot,old),(broot,new)]:
   dynamic=subprocess.check_output(['readelf','-d','--wide',str(root/name)],text=True)
   found=re.findall(r'\(SONAME\).*?\[([^]]+)\]',dynamic)
   if len(found)!=1:raise ValueError('Missing/ambiguous core SONAME: '+name)
   sonames.append(found[0])
   if closure.resolve_image(root,'lib/'+found[0])!=root/name:raise ValueError('Core SONAME alias does not resolve to reviewed implementation')
  if sonames[0]!=sonames[1]:raise ValueError('Core library SONAME drift')
  ae,be=exports(aroot/old),exports(broot/new)
  if ae-be:raise ValueError('Removed library exports: '+str(sorted(ae-be)))
  pairs.append({'control':old,'source':new,'abi_equal':True,'soname':sonames[0],'removed_exports':[],'added_exports':sorted(be-ae),'control_bytes':av['bytes'],'source_bytes':bv['bytes']})
 # Preserve inherited build-directory RPATH findings; refuse any new drift.
 search=lambda r:{n:re.findall(r'.*\((?:RPATH|RUNPATH)\).*',v['elf']) for n,v in r['elf_files'].items() if re.search(r'\((?:RPATH|RUNPATH)\)',v['elf'])}
 if search(a)!=search(b):raise ValueError('Runtime search-path drift')
 return {'schema':1,'passed':True,'source_sha':a['source_sha'],'control_images':a['images'],'source_images':b['images'],'pairs':pairs,'closure':roots,'inherited_search_paths':search(b),'scope':'ELF metadata, preserved dynamic export names, image hashes and shipped dependency/loader paths; not runtime or full behavioral ABI proof','runtime_verified':False,'production_promoted':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('control');p.add_argument('source');p.add_argument('control_image_zip');p.add_argument('source_image_zip');p.add_argument('output');args=p.parse_args()
 a,b=[json.loads(Path(n).read_text()) for n in [args.control,args.source]]
 with tempfile.TemporaryDirectory(prefix='wr-libc-review-') as tmp:
  paths=[]
  for name,archive,r in [('control',args.control_image_zip,a),('source',args.source_image_zip,b)]:
   dest=Path(tmp)/name;dest.mkdir();paths.append(unpack(archive,r,dest))
  result=review(a,b,*paths)
 Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
 print('PASS reviewed libc renames, dynamic exports, exact image/ELF hashes and dependency/loader paths; runtime unverified')
