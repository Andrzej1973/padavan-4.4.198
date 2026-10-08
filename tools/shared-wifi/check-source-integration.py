#!/usr/bin/env python3
"""Check preparation contracts against the pinned HTTP source; not runtime proof."""
import argparse,hashlib,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
r=a.source/'trunk/user'
s=(r/'httpd/web_ex.c').read_text(encoding='utf-8')
assert s.index('#include "wr-shared-wifi/adapter.h"')<s.index('validate_cgi(webs_t')
u=s[s.index('update_variables_ex('):]
assert u.index('wr_shared_wifi_prepare(')<u.index('svc_pop_list(')
assert s.count('validate_asp_apply(wp, sid, &shared)')==3
assert s.count('validate_cgi(wp, sid, &shared)')==1
assert s.count('validate_cgi(wp, sid, NULL)')==3
assert s.count('value = (char *)wr_shared_wifi_value(shared, name, value);')==2
assert 'legacy_shared.plan.mode != WR_SHARED_INDEPENDENT' in s
assert '(shared.plan.mode != WR_SHARED_INDEPENDENT && *script)' in s
assert 'strcmp(action_mode, "  Save  ")' in s
assert '{"wr_wifi_shared", "", NULL, EVM_RESTART_WIFI2|EVM_RESTART_WIFI5}' in (r/'httpd/variables.c').read_text(encoding='utf-8')
d=(r/'shared/defaults.c').read_text(encoding='utf-8');assert d.index('{ "wr_wifi_shared", "0" }')<d.index('#if BOARD_HAS_5G_RADIO')
for name in ('validate.h','plan.h','adapter.h'):
 assert (r/'httpd/wr-shared-wifi'/name).read_bytes()==(Path(__file__).parent/name).read_bytes()
files=[r/'httpd/web_ex.c',r/'httpd/variables.c',r/'shared/defaults.c']+[r/'httpd/wr-shared-wifi'/n for n in ('validate.h','plan.h','adapter.h')]
before=[hashlib.sha256(f.read_bytes()).digest() for f in files]
result=subprocess.run([sys.executable,str(Path(__file__).parent.parent/'prepare-shared-wifi.py'),str(a.source)],capture_output=True)
assert result.returncode!=0
assert before==[hashlib.sha256(f.read_bytes()).digest() for f in files]
print('PASS HTTP source integration structure: preflight ordering, both radio apply calls, legacy guard, default OFF, repeat refuses without writes')
