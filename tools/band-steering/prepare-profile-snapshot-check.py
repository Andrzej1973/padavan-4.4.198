#!/usr/bin/env python3
"""Exercise the snapshot wrappers extracted from the actual prepared ralink.c."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
rc = a.source / 'trunk/user/rc'
text = (rc / 'ralink.c').read_text()
start = text.index('static const struct wr_band_settings_snapshot *wr_profile_snapshot;')
helper = text[start:text.index('\n#else', start)]
paired_start = text.index('int wr_band_generate_profiles(int enabled)')
paired = text[paired_start:text.index('\n#endif', paired_start)]
test = r'''
#include "wr-band-settings-snapshot.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
static int live_reads, live_writes;
static char live[]="changed";
static char *nvram_safe_get(const char *name) { (void)name;++live_reads;return live; }
static char *nvram_wlan_get(int band,const char *name) { (void)band;return nvram_safe_get(name); }
static void nvram_wlan_set(int band,const char *name,char *value)
{ assert(band==0 && !strcmp(name,"key_type") && !strcmp(value,"1"));++live_writes; }
__HELPER__
static int reader(char *data,int capacity,int temporary)
{
    const char dump[]="rt_ssid=original\0wl_ssid=original\0rt_channel=6\0lan_ipaddr_t=192.168.1.1\0rt_key=2\0rt_key2=abcde\0rt_key_type=0\0";
    assert((capacity==256 || capacity==0x20000) && temporary==1);memcpy(data,dump,sizeof(dump));return 0;
}
static int capture_calls, capture_error, incompatible, fail_band, writes2g, writes5g;
static int wr_band_profile_override = -1;
#define WR_PROFILE_COMPATIBLE 0
static int nvram_getall(char *data,int capacity,int temporary)
{ ++capture_calls;if(capture_error){errno=ENOSPC;return -1;}return reader(data,capacity,temporary); }
static const char *wr_band_profile_setting(int band,const char *name,void *p)
{ (void)p;return wr_profile_wlan_get(band,name); }
static int wr_band_profile_from_settings(int enabled,
    const char *(*get)(int,const char *,void *),void *p)
{ assert(enabled && !strcmp(get(0,"ssid",p),"original") && !strcmp(get(1,"ssid",p),"original"));return incompatible; }
static int gen_ralink_config_2g(int scan)
{ assert(!scan && wr_profile_snapshot && wr_band_profile_override>=0);++writes2g;
  assert(!strcmp(wr_profile_wlan_get(0,"ssid"),"original"));live[0]='X';return fail_band==2?-1:0; }
static int gen_ralink_config_5g(int scan)
{ assert(!scan && wr_profile_snapshot && wr_band_profile_override>=0);++writes5g;
  assert(!strcmp(wr_profile_wlan_get(1,"ssid"),"original"));return fail_band==5?-1:0; }
__PAIRED__
int main(void)
{
    struct wr_band_settings_snapshot s={0};
    char before[256];
    assert(!strcmp(wr_profile_safe_get("lan_ipaddr_t"),"changed") && live_reads==1);
    wr_profile_wlan_set(0,"key_type","1");assert(live_writes==1);
    assert(wr_band_profile_bind_snapshot(NULL)==-1);
    assert(wr_band_profile_bind_snapshot(&s)==-1);
    assert(!wr_band_snapshot_capture(&s,256,reader));memcpy(before,s.data,sizeof(before));
    assert(!wr_band_profile_bind_snapshot(&s));
    assert(wr_band_profile_bind_snapshot(&s)==-1);
    assert(!strcmp(wr_profile_wlan_get(0,"ssid"),"original"));
    assert(!strcmp(wr_profile_wlan_get(1,"ssid"),"original"));
    assert(!strcmp(wr_profile_safe_get("lan_ipaddr_t"),"192.168.1.1"));
    assert(wr_profile_wlan_get_int(0,"channel")==6);
    assert(wr_profile_wlan_get_int(0,"missing")==0);
    assert(!strcmp(wr_profile_safe_get("missing"),""));
    assert(!strcmp(wr_profile_wlan_get(0,"key_type"),"1"));
    wr_profile_wlan_set(0,"key_type","1");
    assert(live_reads==1 && live_writes==1 && !memcmp(before,s.data,sizeof(before)));
    wr_band_profile_unbind_snapshot();
    assert(!strcmp(wr_profile_wlan_get(1,"ssid"),"changed") && live_reads==2);
    wr_profile_wlan_set(0,"key_type","1");assert(live_writes==2);
    assert(!wr_band_profile_bind_snapshot(&s));wr_band_profile_unbind_snapshot();
    wr_band_snapshot_release(&s);
    assert(!wr_band_generate_profiles(0) && capture_calls==1 && writes2g==1 && writes5g==1);
    assert(!wr_profile_snapshot && wr_band_profile_override==-1 && live_reads==2);
    fail_band=2;
    assert(wr_band_generate_profiles(1)==-1 && writes2g==2 && writes5g==1);
    assert(!wr_profile_snapshot && wr_band_profile_override==-1);
    fail_band=5;
    assert(wr_band_generate_profiles(1)==-1 && writes2g==3 && writes5g==2);
    assert(!wr_profile_snapshot && wr_band_profile_override==-1);
    incompatible=1;fail_band=0;
    assert(wr_band_generate_profiles(1)==-1 && writes2g==3 && writes5g==2 && !wr_profile_snapshot);
    incompatible=0;capture_error=1;
    assert(wr_band_generate_profiles(0)==-1 && writes2g==3 && writes5g==2 && !wr_profile_snapshot);
    capture_error=0;
    assert(!wr_band_snapshot_capture(&s,256,reader) && !wr_band_profile_bind_snapshot(&s));
    {
        int previous=capture_calls;
        assert(!wr_band_generate_profiles(1) && capture_calls==previous && wr_profile_snapshot==&s);
        fail_band=2;
        assert(wr_band_generate_profiles(1)==-1 && capture_calls==previous && wr_profile_snapshot==&s);
        assert(wr_band_generate_profiles(2)==-1 && wr_profile_snapshot==&s);
    }
    wr_band_profile_unbind_snapshot();wr_band_snapshot_release(&s);
    assert(!wr_profile_snapshot && wr_band_profile_override==-1 && live_reads==2);
    puts("PASS actual ralink snapshot wrappers: fixed reads, derived key type, no live writes, bind rejection and fallback restoration; full transaction pending");
    return 0;
}
'''
a.output.mkdir(parents=True, exist_ok=True)
(a.output / 'profile-snapshot-check.c').write_text(test.replace('__HELPER__', helper).replace('__PAIRED__', paired))
for name in ['wr-band-settings-snapshot.c', 'wr-band-settings-snapshot.h']:
    (a.output / name).write_bytes((rc / name).read_bytes())
