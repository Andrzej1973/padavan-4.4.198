"""Exact ra0/ra1 multicast sysfs transport; real file IO, context actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-multicast-') as d:
 root=Path(d)
 for b in range(2):
  q=root/f'ra{b}'/'brport';q.mkdir(parents=True)
  for attr in ['multicast_fast_leave','multicast_to_unicast']:(q/attr).write_text('0\n')
 code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static int guard=1,foreign,drift,reads;
static int wr_iot_service_guard_dup(void){return guard?dup(1):-1;}
static unsigned fake_index(const char*n){assert(!strcmp(n,"ra0")||!strcmp(n,"ra1"));reads++;return 10+(n[2]-'0')+(drift&&reads>1);}
static ssize_t fake_link(const char*p,char*out,size_t n){(void)p;const char*t=foreign?"../../br9":"../../br0";assert(strlen(t)<n);memcpy(out,t,strlen(t));return strlen(t);}
#define if_nametoindex fake_index
#define readlink fake_link
#define WR_IOT_MULTICAST_SYSFS "ROOT"
#define WR_IOT_SERVICE_GUARD_H
#include "restart-multicast.c"
int main(void){
 assert(!wr_iot_restart_multicast_apply(2,1));assert(!wr_iot_restart_multicast_apply(0,2));
 assert(wr_iot_restart_multicast_current(0,0)&&wr_iot_restart_multicast_current(1,0));
 assert(wr_iot_restart_multicast_apply(0,1)&&wr_iot_restart_multicast_current(0,1));
 assert(wr_iot_restart_multicast_current(1,0));
 foreign=1;assert(!wr_iot_restart_multicast_apply(1,1));foreign=0;
 guard=0;assert(!wr_iot_restart_multicast_apply(1,1));guard=1;
 reads=0;drift=1;assert(!wr_iot_restart_multicast_apply(1,1));drift=0;
 assert(wr_iot_restart_multicast_current(1,0));
 assert(wr_iot_restart_multicast_apply(1,1));
 assert(!unlink(WR_IOT_MULTICAST_SYSFS "/ra1/brport/multicast_to_unicast"));
 assert(!wr_iot_restart_multicast_apply(1,0));
}
'''.replace('ROOT',d)
 p=root/'test.c';p.write_text(code);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS per-BSS multicast transport: actual file writes/readback for both SDK attributes, ra0/ra1 independence, ra2/invalid policy/guard/foreign bridge/ifindex drift refusal; sysfs fixtures not kernel/device acceptance')
