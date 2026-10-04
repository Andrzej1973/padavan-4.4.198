#!/usr/bin/env python3
"""Stage ZeroTier guards inside all pinned IPv4/IPv6 filter transactions."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
path = p.parse_args().source / 'trunk/user/rc/firewall_ex.c'
s = path.read_text(encoding='utf-8')
anchor = 'static int\nipt_filter_rules('
helper = r'''#if defined (APP_ZEROTIER)
/* Keep overlay guards in the same restore transaction as the base firewall. */
static void
include_zerotier_filter(FILE *fp, const char *lan_if, int family)
{
	if (!nvram_match("zerotier_enable", "1"))
		return;
	fprintf(fp, ":ZTWR_INPUT - [0:0]\n:ZTWR_FORWARD - [0:0]\n");
	fprintf(fp, "-A INPUT -j ZTWR_INPUT\n-A FORWARD -j ZTWR_FORWARD\n");
	if (family == 6) {
		fprintf(fp, "-A ZTWR_INPUT -i zt+ -p ipv6-icmp --icmpv6-type 135 -j ACCEPT\n");
		fprintf(fp, "-A ZTWR_INPUT -i zt+ -p ipv6-icmp --icmpv6-type 136 -j ACCEPT\n");
	}
	if (nvram_match("zerotier_router_access", "1"))
		fprintf(fp, "-A ZTWR_INPUT -i zt+ -j ACCEPT\n");
	else
		fprintf(fp, "-A ZTWR_INPUT -i zt+ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT\n");
	fprintf(fp, "-A ZTWR_INPUT -i zt+ -j DROP\n");
	if (nvram_match("zerotier_lan_access", "1")) {
		fprintf(fp, "-A ZTWR_FORWARD -i zt+ -o %s -j ACCEPT\n", lan_if);
		fprintf(fp, "-A ZTWR_FORWARD -i %s -o zt+ -j ACCEPT\n", lan_if);
	}
	fprintf(fp, "-A ZTWR_FORWARD -i zt+ -j DROP\n-A ZTWR_FORWARD -o zt+ -j DROP\n");
}
#endif

'''
if s.count(anchor) != 1:
    raise SystemExit('Pinned filter helper anchor mismatch')
s = s.replace(anchor, helper + anchor)
for name, marker, lan, family in (
    ('ipt_filter_rules', '\t// maclist chain', 'lan_if', 4),
    ('ip6t_filter_rules', '\t// maclist chain', 'lan_if', 6),
    ('ipt_filter_default', '\t/* INPUT chain */', 'IFNAME_BR', 4),
    ('ip6t_filter_default', '\t// INPUT chain', 'IFNAME_BR', 6),
):
    start = s.index('\n' + name + '(')
    end = s.index('\n}\n', start)
    body = s[start:end]
    if body.count(marker) != 1:
        raise SystemExit('Pinned filter body anchor mismatch: ' + name)
    call = '#if defined (APP_ZEROTIER)\n\tinclude_zerotier_filter(fp, %s, %d);\n#endif\n\n' % (lan, family)
    body = body.replace(marker, call + marker)
    s = s[:start] + body + s[end:]
with path.open('w', encoding='utf-8', newline='\n') as out:
    out.write(s)
print('Staged overlay guards in four base firewall filter transactions')
