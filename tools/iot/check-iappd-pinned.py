"""Pinned full IAPP script transformation; syntax/mode/unrelated bytes checks."""
from pathlib import Path
import argparse,hashlib,runpy,subprocess,tarfile,tempfile
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=Path('/home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar'));a=p.parse_args()
transform=runpy.run_path(str(here/'prepare-iappd.py'))['transform']
with tarfile.open(a.archive) as t:
 members=[m for m in t if m.name.endswith('/user/ralinkiappd/iappd.sh')]
 assert len(members)==1 and members[0].isfile()
 raw=t.extractfile(members[0]).read();mode=members[0].mode
source=raw.decode();expected=transform(source)
restored=expected
for proto in ('tcp','udp'):
 old='iptables -A INPUT -i br0 -p '+proto+' --dport 3517 -j ACCEPT'
 replacement=old.replace(' -A INPUT',' -C INPUT')+' 2>/dev/null || '+old
 assert restored.count(replacement)==1
 restored=restored.replace(replacement,old,1)
assert restored.encode()==raw
with tempfile.TemporaryDirectory(prefix='wr-iappd-pinned-') as d:
 f=Path(d)/'iappd.sh';f.write_bytes(raw);f.chmod(mode)
 subprocess.run(['python3','-B',str(here/'prepare-iappd.py'),str(f)],check=True)
 assert f.read_text()==expected and f.stat().st_mode&0o777==mode&0o777
 subprocess.run(['sh','-n',str(f)],check=True)
 before=f.read_bytes()
 duplicate=subprocess.run(['python3','-B',str(here/'prepare-iappd.py'),str(f)],capture_output=True)
 assert duplicate.returncode and f.read_bytes()==before
print('PASS pinned IAPP script: only two rule substitutions, rest byte-identical, executable mode preserved, shell syntax valid, duplicate preparation leaves file unchanged; source SHA256='+hashlib.sha256(raw).hexdigest())
