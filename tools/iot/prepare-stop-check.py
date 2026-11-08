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
prefix=r"""#include <assert.h>
#include <string.h>
#include <stdio.h>
static int owner,gate,answer,controller_calls,calls,leds,refuse_second;
static int auth_stops,auth_starts,starts,profiles,writes,isolations,wan_checks,vga_checks,iapp;
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
#define LED_ON 1
#define LED_CONTROL(a,b) ((void)(a),(void)(b),leds++)
static void wif_control(const char *name,int up){assert(!up&&calls<16);names[calls++]=name;}
#if defined(BOARD_WR1200JS)
static int wr_iot_last_stop_result=1;
static int nvram_match(const char *key,const char *value){assert(strstr(key,"wr_iot_")==key);return !gate&&!strcmp(value,"0");}
static int wr_iot_bridge_is_owned(void){return owner;}
static int wr_iot_activation_prepare_radio_stop(void){controller_calls++;return refuse_second&&controller_calls==2?0:answer;}
"""
mocks=r"""
static void stop_8021x_rt(void){auth_stops++;}
static void start_8021x_rt(void){auth_starts++;}
static void gen_ralink_config_2g(int x){assert(!x);profiles++;}
static int nvram_set_int_temp(const char *key,int value){assert(!strcmp(key,"reload_svc_rt")&&value==1);writes++;return 0;}
static void start_wifi_ap_rt(int on){assert(on==0||on==1);starts++;}
static void start_wifi_wds_rt(int on){assert(on==0||on==1);starts++;}
static void start_wifi_apcli_rt(int on){assert(on==0||on==1);starts++;}
static void restart_guest_lan_isolation(void){isolations++;}
static void check_apcli_wan(int band,int on){assert(band==0&&(on==0||on==1));wan_checks++;}
static void update_vga_clamp_rt(int x){assert(!x);vga_checks++;}
static int system(const char *cmd){assert(!strcmp(cmd,"/usr/bin/iappd.sh restart"));iapp++;return 0;}
"""
tail=r"""
static void baseline(void){
 const char *expected[]={"apcli0","wds3","wds2","wds1","wds0","ra1","ra0"};
 assert(calls==7&&leds==1);
 for(int i=0;i<7;i++)assert(!strcmp(names[i],expected[i]));
}
static void reset_counts(void){
 controller_calls=calls=leds=auth_stops=auth_starts=starts=profiles=writes=isolations=wan_checks=vga_checks=iapp=0;
}
int main(void){
 for(int o=0;o<2;o++)for(int g=0;g<2;g++)for(int a=-1;a<=2;a++){
  owner=o;gate=g;answer=a;refuse_second=0;reset_counts();
  stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
  if(!(o||g)||a==1)baseline();else assert(!calls&&!leds);
  assert(controller_calls==(o||g));
#else
  baseline();assert(!controller_calls);
#endif
  for(int radio=0;radio<2;radio++)for(int reload=0;reload<2;reload++){
   reset_counts();restart_wifi_rt(radio,reload);
#if defined(BOARD_WR1200JS)
   if((o||g)&&a!=1){
    assert(controller_calls==1&&!calls&&!leds&&!auth_stops&&!auth_starts&&!starts&&!profiles&&!writes&&!isolations&&!wan_checks&&!vga_checks&&!iapp);continue;
   }
   assert(controller_calls==2*(o||g));
#else
   assert(!controller_calls);
#endif
   assert(calls==7&&leds==1+radio&&auth_stops==1&&auth_starts==1&&starts==3&&profiles==reload&&writes==reload&&isolations==1&&wan_checks==1&&vga_checks==radio&&iapp==1);
  }
 }
#if defined(BOARD_WR1200JS)
 owner=1;gate=1;answer=1;refuse_second=1;reset_counts();restart_wifi_rt(1,1);
 assert(controller_calls==2&&auth_stops==1&&!calls&&!leds&&!auth_starts&&!starts&&!profiles&&!writes&&!isolations&&!wan_checks&&!vga_checks&&!iapp);
#endif
 puts("PASS full actual RC stop/restart: first/second controller refusal fences physical operations, profile and reopen; radio/reload combinations and other-board behavior preserved; backend unbound");
}

"""
a.output.write_text(prefix+helper+'\n#endif\n'+stop+'\n'+mocks+'\n'+restart+'\n'+tail,encoding='utf-8')
