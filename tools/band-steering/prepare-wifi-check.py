"""Extract actual prepared rc callbacks; host mocks never operate a router."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();rc=a.source/'trunk/user/rc';s=(rc/'net_wifi.c').read_text()
start=s.index('static struct wr_band_service_owner wr_wifi_owner;')
helper=s[start:s.index('\n#endif',start)]
test=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "wr-band-service-owner.h"
#include "wr-band-profile-policy.h"
#define IFNAME_2G_MAIN "ra0"
#define IFNAME_5G_MAIN "rai0"
static int calls[32], count, incompatible, write_failed, interface_failed;
static int requested;
static int boot_ready;
static int stop_failed;
static int off_failed, active_failed, last_state, last_off;
static void mark(int v);
int wr_band_service_quiesce(struct wr_band_service_owner *owner,const char *a,const char *b)
{ assert(owner && !strcmp(a,IFNAME_2G_MAIN) && !strcmp(b,IFNAME_5G_MAIN)); mark(9); if(!stop_failed)owner->pid=0;return stop_failed; }
static int nvram_match(const char *key,const char *value)
{ assert(!strcmp(value,"1")); if(!strcmp(key,"wr_bs_boot_profiles_ready"))return boot_ready;assert(!strcmp(key,"wr_bs_enable"));return requested; }
static int get_enabled_radio_rt(void) { return 1; }
static int get_enabled_radio_wl(void) { return 1; }
static int is_radio_allowed_rt(void) { return 1; }
static int is_radio_allowed_wl(void) { return 1; }
static void logmessage(const char *name,const char *format,...)
{ assert(name && format); }
static void mark(int v) { assert(count<32); calls[count++]=v; }
static const char *nvram_wlan_get(int band, const char *key)
{ assert((band==0||band==1) && key); return "fixture"; }
int wr_band_profile_from_settings(int enabled, wr_band_setting_getter get, void *p)
{ assert(enabled==1 && !strcmp(get(0,"ssid",p),"fixture")); mark(1); return incompatible ? WR_PROFILE_MISMATCH : WR_PROFILE_COMPATIBLE; }
int wr_band_generate_profiles(int enabled)
{ assert(enabled==0||enabled==1); mark(3); return write_failed; }
static void nvram_set_int_temp(const char *key,int value)
{
 if (!strcmp(key,"reload_svc_rt")||!strcmp(key,"reload_svc_wl")) assert(value==1);
 else if (!strcmp(key,"wr_bs_apply_state")) last_state=value;
 else { assert(!strcmp(key,"wr_bs_off_confirmed"));last_off=value; }
}
static void restart_wifi_rt(int on,int reload) { assert((on==0||on==1)&&!reload);mark(4); }
static void restart_wifi_wl(int on,int reload) { assert((on==0||on==1)&&!reload);mark(5); }
static int is_interface_up(const char *name)
{ mark(!strcmp(name,IFNAME_2G_MAIN)?6:7); return !interface_failed; }
static int off(void *p) { (void)p;mark(2);return off_failed; }
static int active(void *p) { (void)p;mark(8);return active_failed; }
int wr_band_service_apply(struct wr_band_service_owner *owner,const char *a,const char *b,
 const struct wr_band_lifecycle_ops *ops,void *context,int enabled,struct wr_band_apply_result *r)
{
 struct wr_band_lifecycle_ops actual=*ops;
 assert(owner && !strcmp(a,IFNAME_2G_MAIN) && !strcmp(b,IFNAME_5G_MAIN));
 actual.quiesce_verified=off;actual.start_verified=active;
 return wr_band_lifecycle_apply(&actual,context,enabled,r);
}
__HELPER__
int main(void)
{
 struct wr_band_apply_result r;
 const int sequence[]={1,2,3,4,5,6,7,8};
 assert(!wr_band_apply_wifi_settings(1,1,1,&r));
 assert(count==8 && !memcmp(calls,sequence,sizeof(sequence)) && r.state==WR_APPLY_RUNNING);
 count=0;incompatible=1;
 assert(wr_band_apply_wifi_settings(1,1,1,&r)==-1 && count==1 && r.state==WR_APPLY_REJECTED);
 count=0;incompatible=0;write_failed=-1;
 assert(wr_band_apply_wifi_settings(1,1,1,&r)==-1 && count==3 && r.state==WR_APPLY_PROFILE_ERROR && r.off_confirmed);
 count=0;write_failed=0;interface_failed=1;
 assert(wr_band_apply_wifi_settings(1,1,1,&r)==-1 && r.state==WR_APPLY_START_ERROR);
 assert(calls[count-1]==2 && r.off_confirmed);
 count=0;interface_failed=0;
 assert(!wr_band_apply_wifi_settings(0,0,0,&r) && r.off_confirmed);
 assert(count==5 && calls[0]==2 && calls[1]==3 && calls[2]==4 && calls[3]==5 && calls[4]==2);
 count=0;
 assert(wr_band_apply_wifi_settings(1,0,1,&r)==-1 && !count);
 assert(wr_band_apply_wifi_settings(0,2,1,&r)==-1 && !count);
 wr_wifi_applying=1;
 assert(wr_band_apply_wifi_settings(0,1,1,&r)==-1 && !count);
 wr_wifi_applying=0;
 assert(!wr_band_handle_wifi_restart(0,1) && !count);
 requested=1;incompatible=1;
 assert(wr_band_handle_wifi_restart(0,1)==1);
 assert(calls[0]==1 && calls[1]==2 && calls[count-1]==2);
 for (int i=0;i<count;++i) assert(calls[i]!=8);
 count=0;requested=0;
 assert(!wr_band_wifi_shutdown() && !count);
 wr_wifi_owner.pid=42;stop_failed=-1;
 assert(wr_band_wifi_shutdown()==-1 && count==1 && calls[0]==9 && wr_wifi_owner.pid==42);
 count=0;stop_failed=0;
 assert(!wr_band_wifi_shutdown() && count==1 && !wr_wifi_owner.pid);
 count=0;
 assert(!wr_band_wifi_startup() && !count);
 requested=1;
 assert(wr_band_wifi_startup()==-1 && !count);
 assert(last_state==WR_APPLY_PROFILE_ERROR && !last_off);
 boot_ready=1;incompatible=0;
 assert(!wr_band_wifi_startup() && calls[count-1]==8);
 assert(last_state==WR_APPLY_RUNNING && !last_off);
 count=0;write_failed=-1;
 assert(wr_band_wifi_startup()==-1 && calls[count-1]==3);
 assert(last_state==WR_APPLY_PROFILE_ERROR && last_off);
 count=0;write_failed=0;active_failed=-1;
 assert(wr_band_wifi_startup()==-1 && calls[count-1]==2);
 assert(last_state==WR_APPLY_START_ERROR && last_off);
 count=0;off_failed=-1;
 assert(wr_band_wifi_startup()==-1 && calls[count-1]==2);
 assert(last_state==WR_APPLY_OFF_UNVERIFIED && !last_off);
 count=0;off_failed=active_failed=0;
 assert(!wr_band_wifi_startup() && calls[count-1]==8);
 puts("PASS actual rc callback ordering/failure paths with mocked radio/service operations; device behavior unverified");
 return 0;
}
'''
a.output.mkdir(parents=True,exist_ok=True)
(a.output/'wifi-lifecycle-check.c').write_text(test.replace('__HELPER__',helper))
for name in ['wr-band-service-owner.h','wr-band-profile-policy.h','wr-band-lifecycle.h','wr-band-lifecycle.c']:
    (a.output/name).write_bytes((rc/name).read_bytes())
