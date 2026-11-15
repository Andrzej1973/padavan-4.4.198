"""SDK WAN identity snapshot adapter; names copied before helper reuse."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include "restart-wan-plan.h"
#define BOARD_HAS_5G_RADIO 1
#define IFNAME_2G_APCLI "apcli0"
#define IFNAME_5G_APCLI "apclii0"
static int guard=1,ap,drift,reads;
static const char*man="eth2.2",*wisp;
static char shared[64];
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static const char*get_man_ifname(int band){assert(!band);if(!man)return 0;strcpy(shared,man);return shared;}
static const char*get_apcli_wisp_ifname(void){reads++;if(!wisp)return 0;strcpy(shared,drift&&reads==2?"apclii0":wisp);return shared;}
#include "restart-wan-policy-sdk.inc"
int main(void){
 enum wr_iot_wan_followup p=WR_WAN_INVALID;
 guard=0;assert(!wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_INVALID);guard=1;
 assert(wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_NONE);
 man="apcli0";wisp="apcli0";reads=0;assert(wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_RECONNECT);
 reads=0;assert(wr_iot_rc_restart_wan_plan(0,&p)&&p==WR_WAN_NONE);
 man="eth2.2";reads=0;assert(wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_FULL_RESTART);
 drift=1;reads=0;p=WR_WAN_INVALID;assert(!wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_INVALID);drift=0;
 man=0;assert(!wr_iot_rc_restart_wan_plan(1,&p));
 man="0123456789012345";assert(!wr_iot_rc_restart_wan_plan(1,&p));
 ap=1;assert(wr_iot_rc_restart_wan_plan(1,&p)&&p==WR_WAN_NONE);
 assert(!wr_iot_rc_restart_wan_plan(2,&p));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wan-policy-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS SDK WAN snapshot: copied shared-buffer names, exact APCLI mapping, guard/oversize/missing/MAN-WISP drift refusal, stock follow-up plan only; helpers injected, no network mutation')
