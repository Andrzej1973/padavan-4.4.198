#!/usr/bin/env python3
"""Verify real ccache reuse, strict prefix normalization and workflow save ordering."""
import hashlib,os,re,runpy,shutil,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[1]
unwrap=runpy.run_path(str(here/'kbuild-compiler.py'))['unwrap_ccache']
assert unwrap(['/bin/cc','-c','a.c'])==['/bin/cc','-c','a.c']
assert unwrap(['/usr/bin/ccache','/bin/cc','-c','a.c'])==['/bin/cc','-c','a.c']
for bad in [['/tmp/ccache','/bin/cc'],['ccache'],['ccache','--compiler','/bin/cc']]:
 try:unwrap(bad)
 except RuntimeError:pass
 else:raise AssertionError('Untrusted/malformed cache prefix accepted')
with tempfile.TemporaryDirectory(prefix='wr-ccache-check-') as tmp:
 base=Path(tmp);src=base/'input.c';out=base/'input.o';src.write_text('int cache_probe(int x){return x+3;}\n')
 env=os.environ.copy();env.update(CCACHE_DIR=str(base/'cache'),CCACHE_BASEDIR=tmp,CCACHE_COMPILERCHECK='content')
 cmd=['/usr/bin/ccache',shutil.which('cc'),'-c',str(src),'-o',str(out)]
 subprocess.run(cmd,env=env,check=True);first=hashlib.sha256(out.read_bytes()).hexdigest();out.unlink()
 subprocess.run(cmd,env=env,check=True);assert hashlib.sha256(out.read_bytes()).hexdigest()==first
 stats=subprocess.check_output(['/usr/bin/ccache','--print-stats'],env=env,text=True)
 assert sum(int(line.split()[1]) for line in stats.splitlines() if 'cache_hit' in line.split()[0])>=1
workflow=(root/'.github/workflows/build-padavan-4.4-wr1200js.yml').read_text()
restore=workflow.split('      - name: Restore compiler cache\n',1)[1].split('      - name:',1)[0]
assert all(x in restore for x in ['github.run_id','github.run_attempt','inputs.toolchain_variant'])
assert workflow.index('      - name: Save compiler cache')>workflow.index('      - name: Compile isolated merged IoT MT7603 candidate')
assert workflow.index('      - name: Compiler cache statistics')>workflow.index('      - name: Compile isolated merged IoT MT7603 candidate')
assert 'CC="/usr/bin/ccache $compiler"' in (here/'ci-compile-merged-candidate.sh').read_text()
print('PASS real repeated compilation hits ccache with identical object; strict compiler-prefix normalization and post-candidate rolling save; not CI speed evidence')
