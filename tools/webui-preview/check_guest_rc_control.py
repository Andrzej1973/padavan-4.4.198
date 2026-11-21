#!/usr/bin/env python3
"""Actual pinned Guest control with interface/bridge fixtures; not driver acceptance."""
import pathlib,subprocess,sys,tarfile,tempfile
with tarfile.open(sys.argv[1]) as archive:
    text=archive.extractfile('trunk/user/rc/net_wifi.c').read().decode()
start=text.index('int\ncontrol_guest_rt(');brace=text.index('{',start);end=brace+1;depth=1
while depth:
    depth+=(text[end]=='{')-(text[end]=='}');end+=1
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define IFNAME_2G_MAIN "ra0"
#define IFNAME_2G_GUEST "ra1"
#define IFNAME_BR "br0"
static int radio,mode,main_up,guest_up,fail_ifconfig,changes,bridges,bridge_on,m2u,isolation,logs;
static int get_enabled_radio_rt(void){return radio;}
static int get_mode_radio_rt(void){return mode;}
static int is_interface_up(const char *name){
 if(!strcmp(name,"ra0"))return main_up;
 assert(!strcmp(name,"ra1"));return guest_up;
}
static int wif_control(const char *name,int up){
 assert(!strcmp(name,"ra1"));changes++;
 if(fail_ifconfig)return -1;
 guest_up=up;return 0;
}
static void br_add_del_if(const char *bridge,const char *name,int up){
 assert(!strcmp(bridge,"br0")&&!strcmp(name,"ra1"));bridges++;bridge_on=up;
}
static void wif_control_m2u(int band,const char *name){assert(!band&&!strcmp(name,"ra1"));m2u++;}
static void restart_guest_lan_isolation(void){isolation++;}
static void logmessage(const char *tag,const char *fmt,const char *state){(void)tag;(void)fmt;(void)state;logs++;}
'''
suffix=r'''
static void reset(void){radio=main_up=1;mode=guest_up=fail_ifconfig=changes=bridges=bridge_on=m2u=isolation=logs=0;}
int main(void){
 for(int fault=0;fault<4;fault++){
  reset();if(fault==0)radio=0;if(fault==1)main_up=0;if(fault==2)mode=1;if(fault==3)mode=3;
  assert(!control_guest_rt(1,1));assert(!changes&&!bridges&&!m2u&&!isolation&&!logs);
 }
 reset();assert(control_guest_rt(1,1)==1);assert(guest_up&&changes==1&&bridges==1&&bridge_on&&m2u==1&&isolation==1&&!logs);
 assert(!control_guest_rt(1,1));assert(changes==1&&bridges==2&&m2u==2&&isolation==1);
 assert(control_guest_rt(0,0)==1);assert(!guest_up&&changes==2&&!bridge_on&&isolation==2&&logs==1);
 assert(!control_guest_rt(0,1));assert(changes==2&&isolation==2);
 // Expose baseline limitation: wrapper ignores failed ifconfig; changed != accepted.
 reset();fail_ifconfig=1;assert(control_guest_rt(1,1)==1);
 assert(!guest_up&&bridges==1&&bridge_on&&isolation==1);
 puts("PASS actual Guest RC control: radio/mode/main guards, idempotence, bridge/isolation calls; failed ifconfig still reports changed (legacy limitation), not driver acceptance");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-rc-control-') as scratch:
    p=pathlib.Path(scratch);(p/'fixture.c').write_text(prefix+text[start:end]+suffix)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(p/'fixture.c'),'-o',str(p/'fixture')],check=True)
    subprocess.run([str(p/'fixture')],check=True)
