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
network=a.source/'trunk/user/rc/net.c'
n=network.read_text(encoding='utf-8')
begin='#if defined (USE_HW_NAT)\n\tif (hwnat_allow)\n'
end='\n\thwnat_configure();\n#endif'
if n.count(begin)!=1 or n.count(end)!=1:
 raise ValueError('HNAT module setup anchors changed; no files written')
b=n.index(begin);e=n.index(end,b)
original=n[b:e]
expected=Path(__file__).with_name('wifi-hwnat-original-block.txt').read_text(encoding='utf-8').rstrip('\n')
if original.rstrip('\n')!=expected:
 raise ValueError('HNAT setup block changed; no files written')
replacement=r'''#if defined (USE_HW_NAT)
	if (hwnat_allow) {
		if (!hwnat_loaded) {
			module_smart_load("hw_nat", NULL);
#if defined (USE_MT7615_AP) || defined (USE_MT7915_AP) || defined (USE_MT76X2_AP)
			if (ipv6_nat == 1)
				doSystem("echo 7 1 > /sys/kernel/debug/hnat/hnat_setting");
			else
				doSystem("echo 7 0 > /sys/kernel/debug/hnat/hnat_setting");
#endif
		}
#if defined (USE_MT7615_AP) || defined (USE_MT7915_AP) || defined (USE_MT76X2_AP)
		/* Reapply both registrations even when hw_nat was already loaded. */
		doSystem("iwpriv %s set hw_nat_register=%d", IFNAME_2G_MAIN, hw_nat_mode == 1);
		doSystem("iwpriv %s set hw_nat_register=%d", IFNAME_5G_MAIN, hw_nat_mode == 1);
#endif
	}
'''.rstrip('\n')
n=n[:b]+replacement+n[e:]
f.write_text(s.replace(old,new),encoding='utf-8')
network.write_text(n,encoding='utf-8')
print('Wireless bring-up respects HNAT mode: only mode 1 registers Wi-Fi')
