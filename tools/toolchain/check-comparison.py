#!/usr/bin/env python3
import copy,importlib.util,json,sys,tempfile,tarfile,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
here=Path(__file__).parent

def module(name):
 spec=importlib.util.spec_from_file_location(name,here/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
compare=module('compare-images').compare
base={'source_sha':'a'*40,'variant':'pinned','target':'mipsel-linux-uclibc','compiler':'gcc10.5','configs':{'kernel':{'sha256':'1'}},'images':{'test.trx':{'sha256':'2','bytes':3}},'elf_files':{'sbin/rc':{'sha256':'3','abi':{'class':1}}}}
new=copy.deepcopy(base);new['variant']='source';new['elf_files']['sbin/rc']['sha256']='4'
assert compare(base,new)['software_comparison_passed']
for field,value in [('source_sha','b'*40),('target','x86_64'),('variant','pinned')]:
 bad=copy.deepcopy(new);bad[field]=value
 try:compare(base,bad)
 except ValueError:pass
 else:raise AssertionError(field)
bad=copy.deepcopy(new);bad['configs']['kernel']['sha256']='bad';assert not compare(base,bad)['software_comparison_passed']
bad=copy.deepcopy(new);bad['elf_files']={};assert not compare(base,bad)['software_comparison_passed']
bad=copy.deepcopy(new);bad['elf_files']['sbin/rc']['abi']={'class':2};assert not compare(base,bad)['software_comparison_passed']
installer=module('install-candidate')
with tempfile.TemporaryDirectory(prefix='wr-toolchain-compare-check-') as d:
 p=Path(d)/'candidate.tar.xz';p.write_bytes(b'fixture')
 r={'project_revision':'5ef6a8577ae24be27d8d81b3fe44a587d8491a16','relocation_tested':True,'qemu_user_verified':True,'production_promoted':False,'gcc':'10.5.0','libc':'1.0.48','linux_headers':'4.4.198','archives':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':7}}}
 installer.validate(r,p)
 for key,value in [('qemu_user_verified',False),('production_promoted',True),('project_revision','bad'),('libc','1.0.43')]:
  bad=copy.deepcopy(r);bad[key]=value
  try:installer.validate(bad,p)
  except ValueError:pass
  else:raise AssertionError(key)
 p.write_bytes(b'changed')
 try:installer.validate(r,p)
 except ValueError:pass
 else:raise AssertionError('wrong hash')
paths=module('tool-paths')
with tempfile.TemporaryDirectory(prefix='wr-tool-paths-') as d:
 root=Path(d);(root/'lib/ccache').mkdir(parents=True);(root/'bin').mkdir()
 (root/'lib/ccache/mipsel-linux-uclibc-gcc').touch()
 for name in ['gcc','readelf']:(root/('bin/mipsel-linux-uclibc-'+name)).touch()
 compiler,readelf=paths.select(root)
 assert compiler.parent==root/'bin' and readelf.parent==root/'bin'
 readelf.unlink()
 try:paths.select(root)
 except ValueError:pass
 else:raise AssertionError('Accepted missing binutils')
print('PASS comparison gates, provenance/hash rejection and ccache wrapper vs actual binutils regression')
# Three versioned libc implementation filenames may change only with matched
# image, closure, ABI and export evidence. All other ELF drift still fails.
a=copy.deepcopy(base);b=copy.deepcopy(new)
names=['ld-uClibc','libthread_db','libuClibc']
pairs=[]
for n in names:
 old='lib/'+n+'-1.0.43.so';new_name='lib/'+n+'-1.0.48.so'
 a['elf_files'][old]={'sha256':'old','abi':{'class':1}}
 b['elf_files'][new_name]={'sha256':'new','abi':{'class':1}}
 pairs.append({'control':old,'source':new_name,'abi_equal':True,'removed_exports':[]})
review={'schema':1,'passed':True,'source_sha':a['source_sha'],'control_images':a['images'],'source_images':b['images'],'pairs':pairs,'closure':{lane:{'errors':[],'elf_count':len(a['elf_files'])} for lane in ['control','source']}}
assert not compare(a,b)['software_comparison_passed']
assert compare(a,b,review)['software_comparison_passed']
for edit in ['source','images','closure','exports','pairs']:
 bad=copy.deepcopy(review)
 if edit=='source':bad['source_sha']='b'*40
 if edit=='images':bad['source_images']={}
 if edit=='closure':bad['closure']['source']['errors']=['missing libc.so.0']
 if edit=='exports':bad['pairs'][0]['removed_exports']=['required_symbol']
 if edit=='pairs':bad['pairs'].pop()
 try:compare(a,b,bad)
 except ValueError:pass
 else:raise AssertionError('Accepted invalid libc review '+edit)
bad=copy.deepcopy(b);bad['elf_files']['unexpected.so']={'sha256':'x','abi':{}}
recheck=copy.deepcopy(review);recheck['closure']['source']['elf_count']+=1
assert not compare(a,bad,recheck)['software_comparison_passed']
bad=copy.deepcopy(b);bad['configs']['extra']={'sha256':'x'}
assert not compare(a,bad,review)['software_comparison_passed']
print('PASS reviewed libc rename gates; absent/mismatched review, closure/export failures, unexpected ELF and extra config rejected')
