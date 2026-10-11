#!/usr/bin/env python3
"""Extract actual prepared RC stop code into a behavior fixture; no device proof."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/net_wifi.c').read_text(encoding='utf-8')
def function(anchor):
 start=s.index(anchor);opening=s.index('{',start);depth=1;end=opening+1
 while depth:
  if s[end]=='{':depth+=1
  elif s[end]=='}':depth-=1
  end+=1
 return s[start:end]
helper=function('static int wr_iot_quiesce(void)')
stop=function('void \nstop_wifi_all_rt(void)')
assert stop.index('wr_iot_last_stop_result=wr_iot_quiesce();')<stop.index('wif_control(IFNAME_2G_APCLI, 0);')
restart=function('void\nrestart_wifi_rt(int radio_on, int need_reload_conf)')
assert restart.index('if (!wr_iot_quiesce()) return;')<restart.index('stop_8021x_rt();')<restart.index('gen_ralink_config_2g(0);')
assert restart.index('stop_wifi_all_rt();')<restart.index('if (!wr_iot_last_stop_result) return;')<restart.index('gen_ralink_config_2g(0);')
# Execute the exact installed restart preflight; the remainder is represented
# by a marker, not a claim that the full radio startup was exercised.
restart_entry=restart[:restart.index('\tstop_8021x_rt();')]+'''\n (void)radio_on;(void)need_reload_conf;restart_progress++;\n}\n'''
prefix=r"""#include <assert.h>
#include <string.h>
#include <stdio.h>
static int owner,detach_ok,down_ok,bss_ok,downs,calls,detaches,logs,leds,profile_state,network_state,state_writes;
static const char *names[16];
static int restart_progress;
#define IFNAME_2G_APCLI "apcli0"
#define IFNAME_2G_WDS3 "wds3"
#define IFNAME_2G_WDS2 "wds2"
#define IFNAME_2G_WDS1 "wds1"
#define IFNAME_2G_WDS0 "wds0"
#define IFNAME_2G_GUEST "ra1"
#define IFNAME_2G_MAIN "ra0"
#define LED_SW2G 0
#define LED_OFF 0
#define LED_CONTROL(a,b) ((void)(a),(void)(b),leds++)
static void wif_control(const char *name,int up){assert(up==0&&calls<16);names[calls++]=name;}
#if defined(BOARD_WR1200JS)
static int wr_iot_last_stop_result=1;
static int nvram_get_int(const char *key){if(!strcmp(key,"wr_iot_network_t"))return network_state;assert(!strcmp(key,"wr_iot_profile_t"));return profile_state;}
static void nvram_set_int_temp(const char *key,int value){assert(value==0&&calls==1&&bss_ok&&down_ok&&detach_ok&&detaches==1);if(!strcmp(key,"wr_iot_network_t"))network_state=value;else {assert(!strcmp(key,"wr_iot_profile_t"));profile_state=value;}state_writes++;}
static int wr_iot_bridge_is_owned(void){return owner;}
static int wr_iot_bss_set_down(void){assert(calls==1&&!strcmp(names[0],"ra2"));return bss_ok;}
static int wr_iot_bridge_set_up(int enabled){assert(enabled==0&&calls==1&&!strcmp(names[0],"ra2")&&!detaches);downs++;return down_ok;}
static int wr_iot_bridge_detach(void){assert(calls==1&&!strcmp(names[0],"ra2")&&downs==1&&down_ok);detaches++;return detach_ok;}
static void logmessage(const char *tag,const char *text){assert(!strcmp(tag,"IoT Wi-Fi")&&strstr(text,"isolation"));logs++;}
"""
tail=r"""
static void reset(int owned,int result){owner=owned;detach_ok=result;down_ok=bss_ok=1;downs=0;calls=detaches=logs=leds=profile_state=network_state=state_writes=0;}
static void baseline(int offset){
 const char *expected[]={"apcli0","wds3","wds2","wds1","wds0","ra1","ra0"};int i;
 assert(calls==7+offset&&leds==1);
 for(i=0;i<7;i++)assert(!strcmp(names[i+offset],expected[i]));
}
int main(void){
 reset(0,1);stop_wifi_all_rt();baseline(0);assert(!detaches&&!logs);
 reset(0,1);profile_state=1;stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
 baseline(1);
 assert(!profile_state&&state_writes==1);
#else
 baseline(0);
 assert(profile_state==1&&!state_writes);
#endif
 reset(0,1);network_state=1;stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
 baseline(1);
 assert(!network_state&&state_writes==1);
#else
 baseline(0);
 assert(network_state==1&&!state_writes);
#endif
 reset(1,1);profile_state=network_state=1;stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
 baseline(1);assert(downs==1&&!strcmp(names[0],"ra2")&&detaches==1&&!logs&&!profile_state&&!network_state&&state_writes==2);
 reset(1,0);profile_state=network_state=1;stop_wifi_all_rt();baseline(1);assert(downs==1&&detaches==1&&logs==1&&profile_state&&network_state&&!state_writes);
 reset(1,1);profile_state=network_state=1;down_ok=0;stop_wifi_all_rt();baseline(1);assert(downs==1&&!detaches&&logs==1&&profile_state&&network_state&&!state_writes);
 reset(1,1);profile_state=network_state=1;bss_ok=0;stop_wifi_all_rt();baseline(1);assert(!downs&&!detaches&&logs==1&&profile_state&&network_state&&!state_writes);
 reset(1,1);profile_state=network_state=1;bss_ok=0;assert(!wr_iot_quiesce());assert(calls==1&&!downs&&!detaches&&profile_state&&network_state&&!state_writes);
 reset(1,1);assert(wr_iot_quiesce());assert(downs==1&&detaches==1);
 reset(1,1);profile_state=network_state=1;bss_ok=0;restart_progress=0;
 restart_wifi_rt(1,1);assert(!restart_progress&&profile_state&&network_state&&!state_writes);
 reset(0,1);restart_wifi_rt(1,1);assert(restart_progress==1&&!calls);
#else
 baseline(0);assert(!detaches&&!logs);
#endif
 puts("PASS actual RC stop fixture: original radio stop sequence retained, WR owned BSS quiesced first, failure reported, other boards unchanged");return 0;
}
"""
a.output.write_text(prefix+helper+'\n#endif\n'+stop+'\n'+restart_entry+'\n'+tail,encoding='utf-8')
