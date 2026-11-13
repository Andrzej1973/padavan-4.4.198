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
assert restart.index('if (!wr_iot_quiesce()) goto wr_iot_restart_done;')<restart.index('stop_8021x_rt();')<restart.index('gen_ralink_config_2g(0);')
assert restart.index('stop_wifi_all_rt();')<restart.index('if (!wr_iot_last_stop_result) goto wr_iot_restart_done;')<restart.index('gen_ralink_config_2g(0);')
prefix=r"""#include <assert.h>
#include <string.h>
#include <stdio.h>
static int answer,controller_calls,calls,leds,refuse_second;
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
#define nvram_match(...) forbidden_nvram_shortcut
#define wr_iot_bridge_is_owned(...) forbidden_bridge_shortcut
static int inject_term;
static volatile sig_atomic_t delivered;
static void fence_signal(int sig){if(!wr_iot_rc_shutdown_note(sig))delivered++;}
static int wr_iot_activation_prepare_radio_stop(void){assert(wr_iot_rc_shutdown.active);if(inject_term){inject_term=0;assert(!kill(getpid(),SIGTERM));}controller_calls++;return refuse_second&&controller_calls==2?0:answer;}
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
 for(int a=-1;a<=2;a++){
  answer=a;refuse_second=0;reset_counts();
  stop_wifi_all_rt();
#if defined(BOARD_WR1200JS)
  if(a==1)baseline();else assert(!calls&&!leds);
  assert(controller_calls==1);
#else
  baseline();assert(!controller_calls);
#endif
  for(int radio=0;radio<2;radio++)for(int reload=0;reload<2;reload++){
   reset_counts();restart_wifi_rt(radio,reload);
#if defined(BOARD_WR1200JS)
   if(a!=1){
    assert(controller_calls==1&&!calls&&!leds&&!auth_stops&&!auth_starts&&!starts&&!profiles&&!writes&&!isolations&&!wan_checks&&!vga_checks&&!iapp);continue;
   }
   assert(controller_calls==2);
#else
   assert(!controller_calls);
#endif
   assert(calls==7&&leds==1+radio&&auth_stops==1&&auth_starts==1&&starts==3&&profiles==reload&&writes==reload&&isolations==1&&wan_checks==1&&vga_checks==radio&&iapp==1);
  }
 }
#if defined(BOARD_WR1200JS)
 answer=1;refuse_second=1;reset_counts();restart_wifi_rt(1,1);
 assert(controller_calls==2&&auth_stops==1&&!calls&&!leds&&!auth_starts&&!starts&&!profiles&&!writes&&!isolations&&!wan_checks&&!vga_checks&&!iapp);
#endif
#if defined(BOARD_WR1200JS)
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 struct sigaction action={0};action.sa_handler=fence_signal;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,NULL));
 reset_counts();answer=0;refuse_second=0;inject_term=1;
 restart_wifi_rt(1,1);
 assert(delivered==1&&!wr_iot_rc_shutdown.active&&!calls&&!auth_stops&&!profiles);
 reset_counts();answer=1;inject_term=1;
 stop_wifi_all_rt();
 assert(delivered==2&&!wr_iot_rc_shutdown.active&&calls==7);
#endif
 puts("PASS full actual RC stop/restart: first/second controller refusal fences physical operations, profile and reopen; radio/reload combinations and other-board behavior preserved; backend unbound");
}

"""
local=Path(__file__).resolve().parent
fence=(local/'radio-stop-fence.c').read_text()
for name in ('radio-stop-fence.h','rc-shutdown-admission.h'):
 fence=fence.replace('#include "'+name+'"','#include "'+str(local/name)+'"')
prefix=prefix.replace('static int wr_iot_last_stop_result=1;',fence+'\nstruct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;\nstatic int wr_iot_last_stop_result=1;')
a.output.write_text(prefix+helper+'\n#endif\n'+stop+'\n'+mocks+'\n'+restart+'\n'+tail,encoding='utf-8')
