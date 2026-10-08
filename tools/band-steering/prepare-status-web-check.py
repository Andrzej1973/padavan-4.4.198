#!/usr/bin/env python3
"""Extract the actual HTTP status handler for host and target checks."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
s=(a.source/'trunk/user/httpd/web_ex.c').read_text(encoding='utf-8')
b=s.index('static int ej_wr_band_observation(')
e=s.index('\n#endif',b)
actual=s[b:e]
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(r'''#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
typedef void *webs_t;
typedef char char_t;
static int serial_value, state_value, apply_value, reads, race, notifications;
static char output[128];
static int nvram_get_int(const char *key) {
 if (!strcmp(key,"wr_bs_observation_serial")) {
  ++reads; return serial_value+(race && reads==2);
 }
 if (!strcmp(key,"wr_bs_observation")) return state_value;
 assert(!strcmp(key,"wr_bs_apply_state")); return apply_value;
}
static void notify_rc(const char *event) {
 assert(!strcmp(event,"observe_wr_band_steering")); ++notifications;
}
static int websWrite(webs_t wp, const char *format, ...) {
 va_list ap; int n; (void)wp;
 va_start(ap,format); n=vsnprintf(output,sizeof(output),format,ap); va_end(ap);
 assert(n>0 && n<(int)sizeof(output)); return n;
}
''' + actual + r'''
static void check(const char *expected, int refresh) {
 char *args[]={"refresh"}; int before=notifications;
 reads=0;
 ej_wr_band_observation(0,NULL,refresh?1:0,args);
 assert(!strcmp(output,expected));
 assert(notifications-before==refresh);
}
int main(void) {
 serial_value=7; state_value=1; apply_value=5;
 check("{\"serial\":7,\"observation\":1,\"apply\":5}",0);
 check("{\"serial\":7,\"observation\":1,\"apply\":5}",1);
 race=1; check("{\"serial\":0,\"observation\":0,\"apply\":0}",0);
 race=0; serial_value=-1; state_value=3; apply_value=6;
 check("{\"serial\":0,\"observation\":0,\"apply\":0}",0);
 serial_value=8; state_value=2; apply_value=2;
 check("{\"serial\":8,\"observation\":2,\"apply\":2}",0);
 return 0;
}
''',encoding='utf-8')
print('Generated actual HTTP handler checks: JSON, refresh, changed serial, bounds')
