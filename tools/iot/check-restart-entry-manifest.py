#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
rc=a.source/'trunk/user/rc';m=json.loads((a.source/'iot-restart-entry-source.json').read_text())
assert m['board']=='WR1200JS' and m['private_restart_hook_bound'] and not m['production_ready'] and not m['physical_runtime_verified']
assert set(m['source_sha256'])=={'net_wifi.c','wr-iot-rc-backend.c','wr-iot-restart-entry.c','Makefile'}
for name,digest in m['source_sha256'].items():
 assert name in ('net_wifi.c','wr-iot-rc-backend.c','wr-iot-restart-entry.c','Makefile')
 assert hashlib.sha256((rc/name).read_bytes()).hexdigest()==digest,name
s=(rc/'net_wifi.c').read_text();start=s.index('void\nrestart_wifi_rt(');end=s.index('\nint is_need_8021x',start) if '\nint is_need_8021x' in s[start:] else len(s)
body=s[start:end]
assert body.count('WR_IOT_PRIVATE_RESTART_ENTRY')==1
assert body.count('if(!wr_iot_radio_stop_fence_begin(&wr_iot_fence)){wr_iot_last_stop_result=0;return;}')==1
assert body.index('wr_iot_restart_entry(')<body.index('wr_iot_radio_stop_fence_begin(')
assert 'if(wr_iot_restart_entry(radio_on,need_reload_conf))return;' in body
assert (rc/'Makefile').read_text().count('wr-iot-restart-entry.o')==1
print('PASS private restart entry manifest hashes/hook-before-fence/object; source only')
