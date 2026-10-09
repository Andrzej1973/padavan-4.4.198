#!/usr/bin/env python3
"""Compile IoT headers after the actual pinned Padavan shared header."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
service=(a.source/'trunk/user/rc/services_ex.c').read_text(encoding='utf-8')
shared=(a.source/'trunk/user/shared/shutils.h').read_text(encoding='utf-8')
if '# define isblank(c)' not in shared:raise SystemExit('Pinned Padavan isblank declaration changed')
prefix='\n'.join(line for line in service.split('#include "rc.h"',1)[0].splitlines() if line.startswith('#include '))+'\n'
if not prefix.startswith('#include <stdio.h>'):raise SystemExit('RC include order changed')
a.output.mkdir(parents=True,exist_ok=True)
positive=prefix+'#include "shutils.h"\n#include "dns-config.h"\n#include "dns-ready.h"\n#include "dhcp-ready.h"\n#include "dns-sockets.h"\nint main(int argc,char **argv){struct wr_iot_dns_sockets state;return argc==2 ? !wr_iot_dns_selected_sockets(argv[1],&state) : !wr_iot_dns_space(32); }\n'
negative=prefix+'#include "shutils.h"\n#include <ctype.h>\nint main(void){return 0;}\n'
(a.output/'positive.c').write_text(positive,encoding='utf-8')
(a.output/'negative.c').write_text(negative,encoding='utf-8')
print('Prepared actual Padavan shared-header order and negative ctype reproducer')
