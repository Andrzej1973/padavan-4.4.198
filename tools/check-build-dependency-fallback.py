#!/usr/bin/env python3
"""Exercise apt source failover without sudo, network or package mutations."""
import os
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='wr-apt-fallback-') as tmp:
    root = Path(tmp)
    fake = root / 'sudo'
    fake.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
args=sys.argv
assert 'Dir::Etc::sourceparts=-' in args
assert not any('AllowUnauthenticated' in arg or 'trusted=yes' in arg for arg in args)
source=next(arg.split('=',1)[1] for arg in args if arg.startswith('Dir::Etc::sourcelist='))
content=pathlib.Path(source).read_text()
assert '-security main restricted universe multiverse' in content
fallback='mirrors.xtom.com' in content
path=pathlib.Path(os.environ['CALL_LOG'])
with path.open('a') as out:out.write(('fallback' if fallback else 'primary')+' '+('update' if 'update' in args else 'install')+'\\n')
mode=os.environ['CASE']
sys.exit(1 if mode=='fail' or (mode=='fallback' and not fallback) else 0)
''')
    fake.chmod(0o755)
    for case, code, expected in [('success',0,['primary update','primary install']),
            ('fallback',0,['primary update','fallback update','fallback install']),
            ('fail',1,['primary update','fallback update'])]:
        log=root/case
        result=subprocess.run(['bash','tools/install-wr1200js-build-deps.sh'],
            env=dict(os.environ,PATH=tmp+':'+os.environ['PATH'],CASE=case,CALL_LOG=str(log)),
            capture_output=True,text=True,timeout=10)
        assert result.returncode==code,(case,result.stderr)
        assert log.read_text().splitlines()==expected,(case,log.read_text())
print('PASS apt primary success, independent mirror fallback, final failure; security pocket retained')
