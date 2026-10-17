#!/usr/bin/env python3
"""Package independent profile storage/validation without boot or network actions."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--config',required=True,type=Path)
a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_WIREGUARD=y' not in a.config.read_text().splitlines():
 print('Independent VPN profile package omitted: standard WG selector disabled');raise SystemExit(0)
user=a.source/'trunk/user';make=user/'Makefile';target=user/'wr-vpn-profiles'
text=make.read_text();anchor='all: $(patsubst %,%_only,$(dir_y))'
if text.count(anchor)!=1 or 'wr-vpn-profiles' in text or target.exists():
 raise SystemExit('VPN profile package anchor changed; no files written')
files=('Makefile','service.sh','profilectl.c','resources.h','store.c','store.h','validate-client.c','validate-process.c','validate-process.h','link-observation.c','link-observation.h','config-readback.c','runtime-state.c','runtime-state.h','config-transaction.c','config-transaction.h','config-apply.c','config-apply.h','config-plan.c','config-plan.h','plan-report.c','plan-report.h','addr-apply.c','addr-apply.h','route-apply.c','route-apply.h','profile-apply.c','profile-apply.h','dns-apply.c','dns-apply.h','link-actions.c','link-actions.h','link-lifecycle.c','link-lifecycle.h')
payloads={name:(Path(__file__).parent/name).read_text() for name in files}
addition='''# Independent profile data tools; no automatic tunnel activation.
ifeq ($(CONFIG_FIRMWARE_INCLUDE_WIREGUARD),y)
dir_y += wr-vpn-profiles
endif

'''
dependencies='''ifeq ($(CONFIG_FIRMWARE_INCLUDE_WIREGUARD),y)
wr-vpn-profiles_only: wireguard-tools_only
ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)
wr-vpn-profiles_only: amneziawg_only
endif
endif

'''
target.mkdir()
for name,data in payloads.items():(target/name).write_text(data,encoding='utf-8',newline='\n')
make.write_text(text.replace(anchor,addition+anchor+'\n\n'+dependencies,1),encoding='utf-8',newline='\n')
print('Prepared WG/AWG profile CLI and pinned native validators; no boot/network hooks')
