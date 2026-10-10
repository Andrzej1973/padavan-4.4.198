#!/usr/bin/env python3
"""Compile the untouched shared header using the prepared ralink prefix."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('prepared',type=Path)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
s=(a.prepared/'trunk/user/httpd/ralink.c').read_text()
start=s.index('#if defined(BOARD_WR1200JS)\n#ifndef CONFIG_RT_MAX_CLIENTS')
end=s.index('#include "common.h"',start)
prefix=s[start:end]
header=(a.source/'trunk/user/shared/include/ralink_priv.h').resolve().as_posix()
a.output.write_text('#include <stddef.h>\n#define BOARD_WR1200JS 1\n'+prefix+'#include "'+header+'"\n'+
 '_Static_assert(MAX_NUMBER_OF_MAC==64,"actual shared capacity");\n'+
 '_Static_assert(sizeof(RT_802_11_MAC_ENTRY)==28,"actual shared entry");\n'+
 '_Static_assert(sizeof(RT_802_11_MAC_TABLE)==sizeof(unsigned long)+64*28,"actual shared table");\n'+
 '#if defined(__mips__)\n_Static_assert(sizeof(RT_802_11_MAC_TABLE)==1796,"actual MIPS table");\n#endif\nint main(void){return 0;}\n')
print('Generated actual shared header capacity compile check')
