#!/usr/bin/env python3
"""Stage fixed IAPP rules after existing WR IoT quarantine hooks."""
import argparse
from pathlib import Path

def transform(source):
 if 'WR_IAPP_BUILDER_RULES' in source:raise ValueError('IAPP builder already prepared')
 for name,ending in [('ipt_filter_rules','return 0;'),('ipt_filter_default','return;')]:
  start=source.index('\n'+name+'(');end=source.index('\n}\n',start)+3
  body=source[start:end]
  marker='logmessage("IoT Wi-Fi","Firewall quarantine write failed");'+ending+'}\n#endif\n'
  if body.count(marker)!=1:raise ValueError('Exact quarantine hook required: '+name)
  rules='''#if defined(BOARD_WR1200JS)
 /* WR_IAPP_BUILDER_RULES: after IoT quarantine, fixed LAN bridge only. */
 if(fputs("-A INPUT -i br0 -p tcp --dport 3517 -j ACCEPT\\n"
          "-A INPUT -i br0 -p udp --dport 3517 -j ACCEPT\\n",fp)==EOF){fclose(fp);'''+ending+'''}
#endif
'''
  body=body.replace(marker,marker+rules,1);source=source[:start]+body+source[end:]
 return source

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('firewall',type=Path);a=p.parse_args()
 original=a.firewall.read_text();result=transform(original);a.firewall.write_text(result)
