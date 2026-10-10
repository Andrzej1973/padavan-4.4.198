#!/usr/bin/env python3
"""Verify the actual prepared HTTP feature prefix and emit a target API probe."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('probe',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/httpd/web_ex.c').read_text()
prefix='#ifndef _GNU_SOURCE\n#define _GNU_SOURCE 1\n#endif\n'
assert s.startswith(prefix),'GNU credential API selection must precede actual HTTP headers'
assert 'do_wr_roaming_json' in s and 'wr_device_background_close' in s
assert '{ "wr_rssi.json", "application/json", no_cache_IE, NULL, do_wr_rssi_json, 1 }' in s
assert 'wr_device_collect_rssi(&wr_device_http_rssi,now)' in s
headers=a.source/'trunk/user/httpd/wr-devices'
import re
for header in headers.glob('*.h'):
 for dependency in re.findall(r'#include "([^"/]+)"',header.read_text()):
  assert (headers/dependency).is_file(),(header,dependency)
# Copy the verified production prefix, rather than defining a fixture-only flag.
a.probe.write_text(s[:len(prefix)]+'#include <sys/socket.h>\nint main(void){struct ucred peer={0};return sizeof(peer)==0 || SCM_CREDENTIALS!=2;}\n')
print('PASS actual prepared HTTP feature prefix; credential API compile probe emitted')
