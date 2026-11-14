"""Compile the actual prepared net_wifi AUX adapter in isolation."""
import ast,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
module=ast.parse((here/'prepare-rc.py').read_text())
helper=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a=helper.index('int wr_iot_rc_physical_aux_down(');b=helper.index('\n}',a)+2
body=helper[a:b]
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <string.h>
#define IFNAME_2G_APCLI "apcli0"
#define IFNAME_2G_WDS3 "wds3"
#define IFNAME_2G_WDS2 "wds2"
#define IFNAME_2G_WDS1 "wds1"
#define IFNAME_2G_WDS0 "wds0"
#define IFNAME_2G_GUEST "ra1"
#define IFNAME_2G_MAIN forbidden_main_interface
static const char *expected[]={"apcli0","wds3","wds2","wds1","wds0","ra1"};
static unsigned slot,calls,lookups;
static int absent,lookup_error,down_error;
static unsigned if_nametoindex(const char *name)
{lookups++;assert(!strcmp(name,expected[slot]));if(absent){errno=lookup_error;return 0;}return 7;}
static int wif_control(const char *name,int up)
{assert(!up&&!strcmp(name,expected[slot]));calls++;return down_error;}
'''
tail=r'''
int main(void){
 for(slot=0;slot<6;slot++)assert(wr_iot_rc_physical_aux_down(slot));
 assert(calls==6&&lookups==6);
 assert(!wr_iot_rc_physical_aux_down(6)&&!wr_iot_rc_physical_aux_down(~0U));
 assert(calls==6&&lookups==6);slot=2;
 down_error=-1;assert(!wr_iot_rc_physical_aux_down(slot));down_error=0;
 absent=1;lookup_error=ENODEV;assert(wr_iot_rc_physical_aux_down(slot));
 lookup_error=ENXIO;assert(wr_iot_rc_physical_aux_down(slot));
 lookup_error=EIO;assert(!wr_iot_rc_physical_aux_down(slot));
 assert(calls==7);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-physical-aux-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(prefix+body+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True,timeout=15)
print('PASS actual prepared AUX adapter: fixed six SDK names/order, no Main slot, invalid index/lookup/DOWN errors refuse, absent optional interface administrative only')
