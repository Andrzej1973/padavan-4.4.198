#!/usr/bin/env python3
"""Supply only the RC declarations needed by the request-stage unit probe."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('output',type=Path)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
(a.output/'rc.h').write_text('''#ifndef RC_H
#define RC_H
const char *nvram_safe_get(const char *);
int nvram_set_temp(const char *,const char *);
int nvram_set_int_temp(const char *,int);
#endif
''',encoding='utf-8')
print('Prepared minimal RC declarations for IoT request-stage probe')
