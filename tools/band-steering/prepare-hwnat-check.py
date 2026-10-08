#!/usr/bin/env python3
"""Extract actual wif_control for isolated HNAT mode regression checks."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
s=(a.source/'trunk/user/rc/net_wifi.c').read_text(encoding='utf-8')
b=s.index('static int\nwif_control(')
e=s.index('\nvoid\nmlme_state_wl',b)
actual=s[b:e]
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(r'''#include <assert.h>
#include <stdarg.h>
#include <string.h>
#define USE_MT76X2_AP 1
#define LOGNAME "fixture"
static int mode, module_loaded, calls, registrations, requested;
#define logmessage(...) ((void)0)
static int is_module_loaded(const char *name) { assert(!strcmp(name,"hw_nat")); return module_loaded; }
static int nvram_get_int(const char *name) { assert(!strcmp(name,"hw_nat_mode")); return mode; }
static int doSystem(const char *format, ...) {
 va_list args; const char *iface;
 ++calls; va_start(args,format); iface=va_arg(args,const char *);
 assert(!strcmp(iface,"ra0"));
 if (!strcmp(format,"iwpriv %s set hw_nat_register=%d")) {
  requested=va_arg(args,int); ++registrations;
 } else { assert(!strcmp(format,"ifconfig %s %s 2>/dev/null")); (void)va_arg(args,const char *); }
 va_end(args); return registrations?0:7;
}
''' + actual + r'''
int main(void) {
 int up, loaded;
 for (mode=0; mode<4; ++mode) for (up=0; up<2; ++up) for (loaded=0; loaded<2; ++loaded) {
  int expected=up&&loaded;
  module_loaded=loaded; calls=registrations=0; requested=-1;
  assert(wif_control("ra0",up)==7);
  assert(calls==1+expected && registrations==expected);
  if (expected) assert(requested==(mode==1));
 }
 return 0;
}
''',encoding='utf-8')
print('Generated actual Wi-Fi HNAT helper fixture: 16 mode/up/module cases')
