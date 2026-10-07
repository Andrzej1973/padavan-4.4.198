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
test = r'''
#include "wr-band-settings-snapshot.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
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
    assert(capacity==256 && temporary==1);memcpy(data,dump,sizeof(dump));return 0;
}
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
    puts("PASS actual ralink snapshot wrappers: fixed reads, derived key type, no live writes, bind rejection and fallback restoration; full transaction pending");
    return 0;
}
'''
a.output.mkdir(parents=True, exist_ok=True)
(a.output / 'profile-snapshot-check.c').write_text(test.replace('__HELPER__', helper))
for name in ['wr-band-settings-snapshot.c', 'wr-band-settings-snapshot.h']:
    (a.output / name).write_bytes((rc / name).read_bytes())
