#!/usr/bin/env python3
"""Generate a host/target fixture from the actual prepared rc observer."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
s = (a.source / 'trunk/user/rc/net_wifi.c').read_text(encoding='utf-8')
start = s.index('static unsigned int wr_bs_observation_serial;')
end = s.index('\n#endif', start)
actual = s[start:end]
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(r'''#include <assert.h>
#include <limits.h>
#include <string.h>
struct { int pid; } wr_wifi_owner;
enum { WR_APPLY_OFF_CONFIRMED = 2 };
static int off, state, reply, calls, refreshes, observed, serial, writes;
static void wr_band_wifi_refresh_exit_status(void) { ++refreshes; }
static int nvram_get_int(const char *key) {
 if (!strcmp(key,"wr_bs_off_confirmed")) return off;
 assert(!strcmp(key,"wr_bs_apply_state")); return state;
}
static int wr_band_control_active(int pid) {
 assert(pid == 42); ++calls; return reply;
}
static void nvram_set_int_temp(const char *key, int value) {
 ++writes;
 if (!strcmp(key,"wr_bs_observation")) observed=value;
 else { assert(!strcmp(key,"wr_bs_observation_serial")); serial=value; }
}
''' + actual + r'''
static void check(int expected, int queries) {
 int before=calls, old_refresh=refreshes, old_writes=writes;
 wr_band_wifi_observe_status();
 assert(observed==expected && calls-before==queries);
 assert(refreshes==old_refresh+1 && writes==old_writes+2);
 assert(serial>0);
}
int main(void) {
 wr_wifi_owner.pid=0; check(0,0);
 wr_wifi_owner.pid=1; check(0,0);
 wr_wifi_owner.pid=42; reply=0; check(1,1);
 reply=-1; check(0,1);
 off=1; state=5; check(0,1);
 state=WR_APPLY_OFF_CONFIRMED; check(2,0);
 wr_wifi_owner.pid=0; check(2,0);
 off=0; check(0,0);
 wr_bs_observation_serial=INT_MAX; check(0,0); assert(serial==1);
 return 0;
}
''', encoding='utf-8')
print('Generated actual rc observation fixture: unknown, authenticated ACTIVE, last OFF, serial wrap')
