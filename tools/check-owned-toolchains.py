#!/usr/bin/env python3
"""Offline execute actual workflow fetch blocks: cache and checksum failure paths."""
import hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
registry=json.loads((root/'sources.lock.json').read_text())['sources']
entries={x['id']:x for x in registry}
paths=['build-padavan-4.4-wr1200js.yml','zapret2-candidate.yml','band-steering-abi.yml','mi-mini-radio-probe.yml','build-padavan-4.4-control.yml']
fixture_hash=hashlib.sha256(b'valid toolchain fixture').hexdigest()
for name in paths:
 text=(root/'.github/workflows'/name).read_text()
 item=entries['mipsel-linux-uclibc-control-toolchain' if 'control' in name else 'mipsel-linux-uclibc-toolchain']
 assert item['owned_asset_api'] in text and item['sha256'] in text
 assert 'uses: actions/cache@v6' in text
 assert not re.search(r'https://github.com/(?:vipshmily|hanwckf)/[^\s]+/releases/download/[^\s]*mipsel',text)
 lines=text.splitlines();start=next(i for i,l in enumerate(lines) if l.strip().startswith('toolchain_cache='));end=next(i for i in range(start,len(lines)) if lines[i].strip().startswith('cp -- "$toolchain_cache" '))
 script='\n'.join(l[10:] for l in lines[start:end+1])
 subprocess.run(['bash','-n'],input=script,text=True,check=True)
 # Substitute fixture bytes/hash only; execute the actual shell control flow.
 script=script.replace(item['sha256'],fixture_hash)
 for mode in ['download','cache','corrupt','failure','wrong_hash']:
  with tempfile.TemporaryDirectory(prefix='wr-owned-toolchain-') as d:
   work=Path(d);(work/'bin').mkdir();(work/'padavan-4.4').mkdir()
   cache=work/'.cache/mips-toolchains'/f'{fixture_hash}.tar.xz';cache.parent.mkdir(parents=True)
   if mode in ['cache','corrupt']:cache.write_bytes(b'valid toolchain fixture' if mode=='cache' else b'corrupt')
   fake=work/'bin/curl';fake.write_text('''#!/usr/bin/env python3
import os,sys
from pathlib import Path
assert sys.argv[-1]==os.environ['EXPECTED_URL']
Path('called').write_text('yes')
p=Path(sys.argv[sys.argv.index('--output')+1]);mode=os.environ['CASE']
p.write_bytes(b'valid toolchain fixture' if mode not in ['failure','wrong_hash'] else b'partial')
if mode=='failure':sys.exit(22)
''');fake.chmod(0o755)
   env=dict(os.environ,PATH=str(work/'bin')+os.pathsep+os.environ['PATH'],GITHUB_WORKSPACE=str(work),CASE=mode,EXPECTED_URL=item['owned_asset_api'])
   result=subprocess.run(['bash','-euo','pipefail','-c',script],cwd=work,env=env,capture_output=True,text=True)
   success=mode not in ['failure','wrong_hash'];assert (result.returncode==0)==success,(name,mode,result.stderr)
   assert not Path(str(cache)+'.part').exists(),(name,mode)
   assert (work/'called').exists()==(mode!='cache')
   dest=work/lines[end].strip().split()[-1]
   if success:assert dest.read_bytes()==b'valid toolchain fixture'
   else:assert not dest.exists()
print('PASS five actual workflow blocks: owned assets, verified cache/miss/corruption, network/hash refusal and partial cleanup (25 cases)')
