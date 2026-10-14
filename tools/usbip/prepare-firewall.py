#!/usr/bin/env python3
"""Keep USB/IP LAN restriction inside each atomic filter-table rebuild."""
import argparse
from pathlib import Path

helper = r'''
/* USB/IP port policy is independent of daemon/requested state. */
static void wr_usbip_filter_input(FILE *fp, const char *lan)
{
 size_t n = lan ? strlen(lan) : 0;
 fprintf(fp, "-A INPUT -p tcp --dport 3240 -j WRUSBIP_BASE\n");
 fprintf(fp, "-A WRUSBIP_BASE -i lo -j RETURN\n");
 if(n > 0 && n <= 15 && strcmp(lan,"lo") &&
    strspn(lan,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-") == n)
  fprintf(fp, "-A WRUSBIP_BASE -i %s -j RETURN\n",lan);
 fprintf(fp, "-A WRUSBIP_BASE -j DROP\n");
}
'''
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--config',type=Path,required=True)
a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    print('USB/IP not selected; firewall unchanged')
    raise SystemExit(0)
path=a.source/'trunk/user/rc/firewall_ex.c'
text=path.read_text()
if 'wr_usbip_filter_input' in text:raise SystemExit('USB/IP firewall already prepared')
calls=[]
for name,lan in [('ipt_filter_rules','lan_if'),('ipt_filter_default','IFNAME_BR'),
                 ('ip6t_filter_rules','lan_if'),('ip6t_filter_default','IFNAME_BR')]:
    if text.count('\n'+name+'(')!=1:raise SystemExit('Firewall function anchor changed: '+name)
    start=text.index('\n'+name+'(')
    position=text.index('\tdtype = "INPUT";',start)+len('\tdtype = "INPUT";')
    # The next INPUT initialization must still belong to this function.
    if text.find('\n}\n',start)<position:raise SystemExit('INPUT anchor outside '+name)
    calls.append((position,'\n\twr_usbip_filter_input(fp, '+lan+');'))
    declaration='\tfprintf(fp, ":%s %s [0:0]\\n", "OUTPUT", "ACCEPT");'
    declared=text.index(declaration,start)+len(declaration)
    if declared>position:raise SystemExit('Chain declaration outside filter header')
    calls.append((declared,'\n\tfprintf(fp, ":WRUSBIP_BASE - [0:0]\\n");'))
for position,call in sorted(calls,reverse=True):text=text[:position]+call+text[position:]
anchor='static int\nipt_filter_rules('
if text.count(anchor)!=1:raise SystemExit('Firewall helper anchor changed')
text=text.replace(anchor,helper+'\n'+anchor)
path.write_text(text)
print('Prepared USB/IP policy in four IPv4/IPv6 normal/default filter generators')
