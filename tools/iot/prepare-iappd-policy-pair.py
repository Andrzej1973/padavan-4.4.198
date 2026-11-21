#!/usr/bin/env python3
"""Validate both policy outputs before touching either candidate input."""
from pathlib import Path
import argparse,runpy
here=Path(__file__).resolve().parent
builder=runpy.run_path(str(here/'prepare-iappd-builder.py'))['transform']
def prepare_pair(firewall,script):
 updated=builder(firewall)
 for proto in ('tcp','udp'):
  old='iptables -A INPUT -i br0 -p '+proto+' --dport 3517 -j ACCEPT'
  if script.count(old)!=1 or 'iptables -C INPUT -i br0' in script:
   raise ValueError('Exact unmodified IAPP policy required')
  script=script.replace(old,': # fixed IAPP INPUT policy supplied by WR firewall builders',1)
 return updated,script
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('firewall',type=Path);p.add_argument('script',type=Path);a=p.parse_args()
 if a.firewall.is_symlink() or a.script.is_symlink():raise SystemExit('Refuse symlink input')
 fw,sh=prepare_pair(a.firewall.read_text(),a.script.read_text())
 # Validation is paired; filesystem write failure can still leave partial output.
 # Candidate preparation must discard the tree on any such error.
 a.firewall.write_text(fw);a.script.write_text(sh)
