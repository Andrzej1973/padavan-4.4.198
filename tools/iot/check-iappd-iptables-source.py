"""Verify pinned iptables command parser and check dispatch, not target binary."""
from pathlib import Path
import argparse,hashlib,tarfile
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=Path('/home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar'));a=p.parse_args()
with tarfile.open(a.archive) as t:
 members=[m for m in t if m.name.endswith('/iptables-1.8.7/iptables/iptables.c')]
 assert len(members)==1 and members[0].isfile()
 raw=t.extractfile(members[0]).read();s=raw.decode()
 start=s.index("case 'C':")
 assert 'CMD_CHECK' in s[start:s.index('break;',start)]
 start=s.index('case CMD_CHECK:');end=s.index('break;',start)
 assert 'check_entry(' in s[start:end]
print('PASS pinned iptables1.8.7 source: -C parser selects CMD_CHECK and dispatches check_entry; SHA256='+hashlib.sha256(raw).hexdigest()+'; effective target binary/image/runtime still require verification')
