#!/usr/bin/env python3
"""Prepare fixed-radio observation integration in actual httpd ralink source."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
local = Path(__file__).resolve().parent
http = a.source / 'trunk/user/httpd'
f = http / 'ralink.c'
s = f.read_text(encoding='utf-8')
anchor = 'int \nej_wl_auth_list(int eid, webs_t wp, int argc, char **argv)'
if s.count(anchor) != 1 or 'wr_device_collect_radio' in s:
    raise SystemExit('Radio integration anchor changed; no files written')
include_anchor = '#include "common.h"'
if s.count(include_anchor) != 1:
    raise SystemExit('Shared header anchor changed; no files written')
# Shared ralink_priv.h defaults to 32 when the kernel selector is absent
# from userspace CFLAGS. Set it before any common/shared header is parsed.
capacity = """#if defined(BOARD_WR1200JS)
#ifndef CONFIG_RT_MAX_CLIENTS
#define CONFIG_RT_MAX_CLIENTS 64
#elif CONFIG_RT_MAX_CLIENTS != 64
#error WR1200JS station capacity differs from the driver ABI
#endif
#endif
"""
s = s.replace(include_anchor, capacity + include_anchor, 1)
code = (local / 'radio-hook.inc').read_text(encoding='utf-8')
headers = http / 'wr-devices'
headers.mkdir(exist_ok=True)
for name in ('networkmap.h', 'radio-table.h', 'radio-query.h', 'radio-merge.h'):
    (headers / name).write_bytes((local / name).read_bytes())
f.write_text(s.replace(anchor, code + '\n' + anchor, 1), encoding='utf-8')
print('Prepared WR fixed-radio station collector; HTTP caller wiring remains separate')
