#!/usr/bin/env python3
"""Verify installed paired source hashes and exact rule locations."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
m=json.loads((a.source/'iot-iapp-policy-source.json').read_text())
assert m['iapp_compile_gate_enabled']
assert (a.source/'trunk/user/rc/wr-iot/restart-iapp-policy.h').read_text()=='#define WR_IOT_IAPP_POLICY_PREPARED 1\n'
assert m['board']=='WR1200JS' and not m['production_ready'] and m['iapp_root_launch_bound']
fw=(a.source/'trunk/user/rc/firewall_ex.c').read_bytes();sh=(a.source/'trunk/user/ralinkiappd/iappd.sh').read_bytes()
assert hashlib.sha256(fw).hexdigest()==m['outputs_sha256']['firewall']
assert hashlib.sha256(sh).hexdigest()==m['outputs_sha256']['script']
s=fw.decode()
for name in ('ipt_filter_rules','ipt_filter_default'):
 start=s.index('\n'+name+'(');end=s.index('\n}\n',start);body=s[start:end]
 assert body.count('WR_IAPP_BUILDER_RULES')==1 and body.count('--dport 3517')==2
 assert body.index('wr_iot_firewall_quarantine(')<body.index('WR_IAPP_BUILDER_RULES')
assert 'iptables -A INPUT' not in sh.decode() and sh.decode().count('fixed IAPP INPUT policy supplied')==2
print('PASS installed paired IAPP source hashes/order/removal; no runtime claim')
