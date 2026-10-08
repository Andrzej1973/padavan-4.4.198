#!/usr/bin/env python3
"""Respect the existing HNAT mode when a wireless interface is brought up."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
a=p.parse_args()
f=a.source/'trunk/user/rc/net_wifi.c'
s=f.read_text(encoding='utf-8')
old='doSystem("iwpriv %s set hw_nat_register=%d", wifname, 1);'
new='doSystem("iwpriv %s set hw_nat_register=%d", wifname, nvram_get_int("hw_nat_mode") == 1);'
if s.count(old)!=1 or new in s:
 raise ValueError('Wireless HNAT registration anchor changed; no file written')
f.write_text(s.replace(old,new),encoding='utf-8')
print('Wireless bring-up respects HNAT mode: only mode 1 registers Wi-Fi')
