#!/usr/bin/env python3
"""Offline real Makefile download target fault injection; no compilation/network."""
import hashlib,os,subprocess,tempfile
from pathlib import Path
makefile=Path(__file__).resolve().parent.parent/'overlay/padavan-4.4/ports/stubby/libyaml/Makefile'
with tempfile.TemporaryDirectory(prefix='wr-libyaml-download-') as d:
 root=Path(d);binpath=root/'bin';binpath.mkdir();wget=binpath/'wget'
 wget.write_text('''#!/usr/bin/env python3
import os,sys
from pathlib import Path
url=sys.argv[-1];dest=Path(sys.argv[sys.argv.index('-O')+1])
with open('calls','a') as f:f.write(url+'\\n')
mode=os.environ['CASE']
if mode=='all_fail' or (url=='primary' and mode=='fallback'):
 dest.write_bytes(b'partial');sys.exit(4)
dest.write_bytes(b'wrong' if url=='primary' and mode=='bad_hash' else b'valid')
''');wget.chmod(0o755)
 for case in ['primary','fallback','bad_hash','all_fail','cached','corrupt_cache']:
  work=root/case;work.mkdir();archive=work/'yaml-0.2.5.tar.gz'
  if case in ['cached','corrupt_cache']:archive.write_bytes(b'valid' if case=='cached' else b'corrupt')
  env=dict(os.environ,PATH=str(binpath)+os.pathsep+os.environ['PATH'],CASE=case)
  r=subprocess.run(['make','-f',str(makefile),'download_test','SRC_URL=primary','SRC_FALLBACK_URL=fallback','SRC_SHA256='+hashlib.sha256(b'valid').hexdigest()],cwd=work,env=env,capture_output=True,text=True)
  assert (r.returncode==0)==(case!='all_fail'),(case,r.stdout,r.stderr)
  assert not (work/'yaml-0.2.5.tar.gz.part').exists(),case
  if case=='all_fail':assert not archive.exists()
  else:assert archive.read_bytes()==b'valid'
  calls=(work/'calls').read_text().splitlines() if (work/'calls').exists() else []
  assert calls==([] if case=='cached' else ['primary','fallback'] if case in ['fallback','bad_hash','all_fail'] else ['primary']),(case,calls)
print('PASS actual libyaml Makefile: primary/fallback, hash refusal, partial cleanup, valid cache and corrupt-cache recovery')
