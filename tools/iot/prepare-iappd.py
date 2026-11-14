#!/usr/bin/env python3
"""Make the pinned IAPP INPUT rules idempotent; no lifecycle installation."""
from pathlib import Path
import argparse

def transform(source):
 if "iptables -C INPUT -i br0" in source:raise ValueError("IAPP already prepared")
 for protocol in ('tcp','udp'):
  old='iptables -A INPUT -i br0 -p '+protocol+' --dport 3517 -j ACCEPT'
  if source.count(old)!=1:raise ValueError('IAPP firewall anchor changed: '+protocol)
  check=old.replace(' -A INPUT',' -C INPUT')
  source=source.replace(old,check+' 2>/dev/null || '+old,1)
 return source

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('script',type=Path);a=p.parse_args()
 text=a.script.read_text();result=transform(text);a.script.write_text(result)
