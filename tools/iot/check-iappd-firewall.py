"""Execute transformed fixed IAPP firewall commands twice with command actor."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
transform=runpy.run_path(str(here/'prepare-iappd.py'))['transform']
source='\n'.join('iptables -A INPUT -i br0 -p '+p+' --dport 3517 -j ACCEPT' for p in ('tcp','udp'))+'\n'
result=transform(source)
try:transform(result)
except ValueError:pass
else:raise AssertionError('duplicate preparation accepted')
try:transform(source.replace('--dport 3517','--dport 9999',1))
except ValueError:pass
else:raise AssertionError('changed source accepted')
with tempfile.TemporaryDirectory(prefix='wr-iappd-firewall-') as d:
 root=Path(d);actor=root/'iptables';actor.write_text('''#!/bin/sh
[ "$2 $3 $4 $5 $7 $8 $9" = "INPUT -i br0 -p --dport 3517 -j" ] || exit 90
case "$6" in tcp|udp) ;; *) exit 91;; esac
case "$1" in
-C) test -f "$IAPP_TEST/$6" ;;
-A) echo "$6" >> "$IAPP_TEST/adds"; : > "$IAPP_TEST/$6" ;;
*) exit 92;;
esac
''');actor.chmod(0o700)
 import os
 env=dict(os.environ,PATH=d+':'+os.environ['PATH'],IAPP_TEST=d)
 for _ in range(2):subprocess.run(['sh','-ec',result],env=env,check=True,timeout=5)
 assert (root/'adds').read_text().splitlines()==['tcp','udp']
print('PASS IAPP fixed INPUT rules: transformed shell checks before add, two starts add each TCP/UDP3517 rule once; changed/duplicate source rejected; iptables actor, not kernel acceptance')
