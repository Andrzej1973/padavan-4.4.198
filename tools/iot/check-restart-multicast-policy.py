"""SDK multicast policy in both compile branches, no NVRAM mutation."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "restart-multicast-policy.h"
static int guard=1,ap,mode,radio=1,guest,guest_fail,raw,drift,reads;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int wr_iot_rc_restart_guest_policy(int*out){*out=guest;return !guest_fail;}
#ifndef USE_IGMP_SNOOP
static int nvram_wlan_get_int(int b,const char*k){assert(!b&&!strcmp(k,"IgmpSnEnable"));return raw+(drift&&++reads==2);}
#endif
#include "restart-multicast-policy-sdk.inc"
int main(void){
 struct wr_iot_multicast_policy p={7,7,7};
 guard=0;assert(!wr_iot_rc_restart_multicast_policy(&p)&&p.required==7);guard=1;
 ap=1;assert(!wr_iot_rc_restart_multicast_policy(&p));ap=0;
 mode=2;assert(!wr_iot_rc_restart_multicast_policy(&p));mode=0;
 radio=0;assert(!wr_iot_rc_restart_multicast_policy(&p));radio=1;
 guest_fail=1;assert(!wr_iot_rc_restart_multicast_policy(&p));guest_fail=0;
 for(int g=0;g<2;g++)for(int value=-1;value<3;value++){
  guest=g;raw=value;assert(wr_iot_rc_restart_multicast_policy(&p)&&p.guest==g);
#ifdef USE_IGMP_SNOOP
  assert(!p.required&&!p.enabled);
#else
  assert(p.required&&p.enabled==!!value);
#endif
 }
#ifndef USE_IGMP_SNOOP
 drift=1;reads=0;p.required=7;assert(!wr_iot_rc_restart_multicast_policy(&p)&&p.required==7);
#else
 (void)drift;(void)reads;
#endif
}
'''
with tempfile.TemporaryDirectory(prefix='wr-multicast-policy-') as d:
 p=Path(d)/'test.c';p.write_text(code)
 for snoop in (False,True):
  b=Path(d)/('snoop' if snoop else 'convert')
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)]+(['-DUSE_IGMP_SNOOP'] if snoop else []),check=True)
  subprocess.run([str(b)],check=True,timeout=15)
print('PASS extracted SDK multicast policy in both USE_IGMP_SNOOP branches: guard/mode/radio/Guest gates, exact saved IgmpSnEnable stability and stock boolean semantics; no writes; SDK actors injected')
