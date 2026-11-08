#!/usr/bin/env python3
"""Exercise owned candidate fetch, cached corruption, provenance and failure cleanup."""
import copy,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('candidate_fetch',here/'fetch-owned-candidate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
archive='mipsel-linux-uclibc-source-candidate.tar.xz'
def fixture():
 data={archive:b'candidate fixture'}
 report={'project_revision':'5ef6a8577ae24be27d8d81b3fe44a587d8491a16','relocation_tested':True,'qemu_user_verified':True,'production_promoted':False,'gcc':'10.5.0','libc':'1.0.48','linux_headers':'4.4.198','archives':{archive:{'sha256':hashlib.sha256(data[archive]).hexdigest(),'bytes':len(data[archive])}}}
 data['result.json']=json.dumps(report).encode()
 manifest={'schema':1,'generator_revision':report['project_revision'],'source_run':42467546674,'files':[{'filename':name,'url':'https://api.github.com/repos/Andrzej1973/padavan-4.4.198/releases/assets/'+str(i+1),'sha256':hashlib.sha256(value).hexdigest(),'bytes':len(value)} for i,(name,value) in enumerate(data.items())]}
 return data,manifest
with tempfile.TemporaryDirectory(prefix='wr-owned-candidate-') as d:
 root=Path(d);data,manifest=fixture();calls=[]
 by_url={v['url']:data[v['filename']] for v in manifest['files']}
 def download(url,path):calls.append(url);path.write_bytes(by_url[url])
 m.fetch(root/'out',root/'cache',manifest,download);assert len(calls)==2
 calls.clear();m.fetch(root/'cached',root/'cache',manifest,download);assert not calls
 cached=root/'cache'/(manifest['files'][0]['sha256']+'-'+archive);cached.write_bytes(b'corrupt')
 m.fetch(root/'recovered',root/'cache',manifest,download);assert len(calls)==1
 for mode in ['network','wrong-hash']:
  def bad_download(url,path):
   path.write_bytes(b'partial')
   if mode=='network':raise OSError('injected transport failure')
  try:m.fetch(root/mode,root/(mode+'-cache'),manifest,bad_download)
  except (OSError,ValueError):pass
  else:raise AssertionError(mode)
  assert not list((root/(mode+'-cache')).glob('*.part'))
 for case in ['path','foreign','generator']:
  bad=copy.deepcopy(manifest)
  if case=='path':bad['files'][0]['filename']='../escape'
  if case=='foreign':bad['files'][0]['url']='https://example.com/compiler'
  if case=='generator':bad['generator_revision']='a'*40
  try:m.fetch(root/case,root/(case+'-cache'),bad,download)
  except ValueError:pass
  else:raise AssertionError(case)
 data,manifest=fixture();report=json.loads(data['result.json']);report['qemu_user_verified']=False;data['result.json']=json.dumps(report).encode();item=manifest['files'][1];item['sha256']=hashlib.sha256(data['result.json']).hexdigest();item['bytes']=len(data['result.json']);by_url={v['url']:data[v['filename']] for v in manifest['files']}
 try:m.fetch(root/'unverified',root/'unverified-cache',manifest,download)
 except ValueError:pass
 else:raise AssertionError('Unverified compiler accepted')
print('PASS owned candidate: exact fetch/cache/corruption, network/hash cleanup, foreign/path/provenance rejection')
