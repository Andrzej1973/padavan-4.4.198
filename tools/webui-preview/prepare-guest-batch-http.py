#!/usr/bin/env python3
"""Bind isolated Guest JSON route to one batch ioctl; never install production."""
import argparse
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
here=Path(__file__).resolve().parent
httpd=args.source/'trunk/user/httpd'
web=httpd/'web_ex.c'
source=web.read_text()
old=(here/'guest-json-output.c.inc').read_text()
if source.count(old)!=1:parser.error('Guest JSON output anchor changed')
reply=old[:old.index('static void do_wr_modern_guest_apply(')]
source=source.replace(old,reply+(here/'guest-batch-http.c.inc').read_text(),1)
anchor='#include "wr-shared-wifi/guest-adapter.h"'
if source.count(anchor)!=1:parser.error('Guest include anchor changed')
source=source.replace(anchor,anchor+'\n#include "wr-shared-wifi/guest-batch.h"\n#include "wr-shared-wifi/nvram-batch-client.h"\n#include <fcntl.h>',1)
for name in ('guest-batch.h','nvram-batch-client.h','nvram-batch-wire.h'):
    dest=httpd/'wr-shared-wifi'/name
    if dest.exists():parser.error('Batch header already exists: '+name)
for name in ('guest-batch.h','nvram-batch-client.h','nvram-batch-wire.h'):
    (httpd/'wr-shared-wifi'/name).write_bytes((here/name).read_bytes())
web.write_text(source)
print('Prepared isolated single-batch Guest JSON handler; production/runtime unverified')
