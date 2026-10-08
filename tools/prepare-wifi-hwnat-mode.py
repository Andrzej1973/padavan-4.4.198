#!/usr/bin/env python3
"""Respect the existing HNAT mode when a wireless interface is brought up."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--lan-only-default',action='store_true',help='WR factory default only; never writes live NVRAM')
a=p.parse_args()
f=a.source/'trunk/user/rc/net_wifi.c'
s=f.read_text(encoding='utf-8')
old='doSystem("iwpriv %s set hw_nat_register=%d", wifname, 1);'
getter='nvram_get_int'
if 'static int wr_radio_get_int(const char *name)' in s:
 # Preserve the coordinated apply snapshot when steering adapters are present.
 getter='wr_radio_get_int'
new='doSystem("iwpriv %s set hw_nat_register=%d", wifname, '+getter+'("hw_nat_mode") == 1);' 
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
log_old='hwnat_status = "Enabled, IPoE/PPPoE offload [WAN]<->[LAN/WLAN]";'
if n.count(log_old)!=1:
 raise ValueError('HNAT status label changed; no files written')
n=n.replace(log_old, 'hwnat_status = nvram_get_int("hw_nat_mode") == 1 ?\n'
 '        "Enabled module, requested offload [WAN]<->[LAN/WLAN]" :\n'
 '        "Enabled module, requested offload [WAN]<->[LAN]";')
changes=[(f,s.replace(old,new)),(network,n)]
if a.lan_only_default:
 defaults=a.source/'trunk/user/shared/defaults.c'
 d=defaults.read_text(encoding='utf-8')
 anchor='{ "hw_nat_mode", "1" }'
 if d.count(anchor)!=1:
  raise ValueError('HNAT factory default changed; no files written')
 changes.append((defaults,d.replace(anchor,'{ "hw_nat_mode", "2" }')))
for path,text in changes:
 path.write_text(text,encoding='utf-8')
print('Wireless bring-up respects HNAT mode: only mode 1 registers Wi-Fi')
