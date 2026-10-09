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
helper=function('static void wr_iot_quiesce(void)')
stop=function('void \nstop_wifi_all_rt(void)')
assert stop.index('wr_iot_quiesce();')<stop.index('wif_control(IFNAME_2G_APCLI, 0);')
prefix=r"""#include <assert.h>
#include <string.h>
#include <stdio.h>
static int owner,detach_ok,calls,detaches,logs,leds;
static const char *names[16];
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
static int wr_iot_bridge_is_owned(void){return owner;}
static int wr_iot_bridge_detach(void){assert(calls==1&&!strcmp(names[0],"ra2"));detaches++;return detach_ok;}
static void logmessage(const char *tag,const char *text){assert(!strcmp(tag,"IoT Wi-Fi")&&strstr(text,"isolation"));logs++;}
"""
tail=r"""
static void reset(int owned,int result){owner=owned;detach_ok=result;calls=detaches=logs=leds=0;}
static void baseline(int offset){
 const char *expected[]={"apcli0","wds3","wds2","wds1","wds0","ra1","ra0"};int i;
 assert(calls==7+offset&&leds==1);
 for(i=0;i<7;i++)assert(!strcmp(names[i+offset],expected[i]));
}
int main(void){
 reset(0,1);stop_wifi_all_rt();baseline(0);assert(!detaches&&!logs);
 reset(1,1);stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
 baseline(1);assert(!strcmp(names[0],"ra2")&&detaches==1&&!logs);
 reset(1,0);stop_wifi_all_rt();baseline(1);assert(detaches==1&&logs==1);
#else
 baseline(0);assert(!detaches&&!logs);
#endif
 puts("PASS actual RC stop fixture: original radio stop sequence retained, WR owned BSS quiesced first, failure reported, other boards unchanged");return 0;
}
"""
a.output.write_text(prefix+helper+'\n#endif\n'+stop+'\n'+tail,encoding='utf-8')
