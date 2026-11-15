"""Exact SDK builder bodies plus actual quarantine-hook installer, source only."""
from pathlib import Path
import ast,hashlib,runpy,tarfile,argparse
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=Path('/home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar'));a=p.parse_args()
with tarfile.open(a.archive) as t:
 m=next(m for m in t if m.name.endswith('/user/rc/firewall_ex.c'));raw=t.extractfile(m).read()
 script=t.extractfile(next(m for m in t if m.name.endswith('/user/ralinkiappd/iappd.sh'))).read().decode()
firewall=raw.decode()
tree=ast.parse((here/'prepare-rc.py').read_text())
loops=[n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [getattr(x,'id','') for x in n.target.elts]==['name','marker','result','arguments']]
assert len(loops)==1
ns={'firewall':firewall};exec(compile(ast.Module(body=loops,type_ignores=[]),'<actual quarantine installer>','exec'),ns)
prepared=ns['firewall'];transform=runpy.run_path(str(here/'prepare-iappd-builder.py'))['transform'];result=transform(prepared)
for name in ('ipt_filter_rules','ipt_filter_default'):
 start=result.index('\n'+name+'(');end=result.index('\n}\n',start);body=result[start:end]
 assert body.count('WR_IAPP_BUILDER_RULES')==1
 assert body.index('wr_iot_firewall_quarantine(')<body.index('WR_IAPP_BUILDER_RULES')
 assert body.count('--dport 3517')==2
for name in ('ip6t_filter_rules','ip6t_filter_default'):
 start=result.index('\n'+name+'(');end=result.index('\n}\n',start)
 assert 'WR_IAPP_BUILDER_RULES' not in result[start:end]
print('PASS exact SDK firewall bodies plus actual quarantine installer/IAPP transform: IPv4 hooks once after quarantine, IPv6 unchanged; source composition only, full SDK compile/image pending; input SHA256='+hashlib.sha256(raw).hexdigest())

pair=runpy.run_path(str(here/'prepare-iappd-policy-pair.py'))['prepare_pair']
paired_fw,paired_script=pair(prepared,script)
assert paired_fw==result and 'iptables -A INPUT' not in paired_script
assert paired_script.count('fixed IAPP INPUT policy supplied')==2
try:pair(prepared,script.replace('--dport 3517','--dport 9999',1))
except ValueError:pass
else:raise AssertionError('changed script accepted')
import subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='wr-iapp-pair-') as d:
 p=Path(d)/'iappd.sh';p.write_text(paired_script);subprocess.run(['sh','-n',str(p)],check=True)
print('PASS paired exact SDK policy preparation: builder rules and script removal validated together, changed input refuses, resulting script syntax valid; not installed')
