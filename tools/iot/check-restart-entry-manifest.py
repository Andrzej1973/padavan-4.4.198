#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
rc=a.source/'trunk/user/rc';m=json.loads((a.source/'iot-restart-entry-source.json').read_text())
assert m['owned_restart_refusal_no_fallback'] is True
assert m['board']=='WR1200JS' and m['private_restart_hook_bound'] and not m['production_ready'] and not m['physical_runtime_verified']
assert set(m['source_sha256'])=={'net_wifi.c','wr-iot-rc-backend.c','wr-iot-restart-entry.c','wr-iot-initial-restart-entry.c','Makefile'}
for name,digest in m['source_sha256'].items():
 assert name in ('net_wifi.c','wr-iot-rc-backend.c','wr-iot-restart-entry.c','wr-iot-initial-restart-entry.c','Makefile')
 assert hashlib.sha256((rc/name).read_bytes()).hexdigest()==digest,name
s=(rc/'net_wifi.c').read_text();start=s.index('void\nrestart_wifi_rt(');end=s.index('\nint is_need_8021x',start) if '\nint is_need_8021x' in s[start:] else len(s)
body=s[start:end]
assert body.count('WR_IOT_PRIVATE_RESTART_ENTRY')==1
assert body.count('if(!wr_iot_radio_stop_fence_begin(&wr_iot_fence)){wr_iot_last_stop_result=0;return;}')==1
assert m['historical_radio_on_hook_bound'] and m['owned_radio_off_hook_bound']
assert m['cold_radio_on_hook_bound'] and m['initial_restart_hook_bound']
assert (rc/'wr-iot/radio-entry-result.h').read_bytes()==(Path(__file__).resolve().parent/'radio-entry-result.h').read_bytes()
assert (rc/'wr-iot/restart-entry.h').read_bytes()==(Path(__file__).resolve().parent/'restart-entry.h').read_bytes()
assert 'return wr_iot_cold_on_entry(radio_on,reload);' in (rc/'wr-iot-restart-entry.c').read_text()
assert body.index('wr_iot_radio_off_entry(')<body.index('wr_iot_radio_on_entry(')<body.index('wr_iot_initial_restart_entry(')<body.index('wr_iot_restart_entry(')<body.index('wr_iot_radio_stop_fence_begin(')
assert 'if(wr_iot_radio_on_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;' in body
assert 'if(wr_iot_restart_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;' in body
assert (rc/'Makefile').read_text().count('wr-iot-restart-entry.o')==1
print('PASS private restart entry manifest hashes/hook-before-fence/object; source only')

assert 'if(wr_iot_initial_restart_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;' in body
assert (rc/'Makefile').read_text().count('wr-iot-initial-restart-entry.o')==1
assert (rc/'wr-iot/initial-restart-entry.h').read_bytes()==(Path(__file__).resolve().parent/'initial-restart-entry.h').read_bytes()
