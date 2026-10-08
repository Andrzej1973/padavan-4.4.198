#!/usr/bin/env python3
"""Extract actual original-radio settings adapters for isolated verification."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
rc = a.source / 'trunk/user/rc'
text = (rc / 'net_wifi.c').read_text()
start = text.index('static const struct wr_band_settings_snapshot *wr_radio_snapshot;')
helper = text[start:text.index('\n#else', start)]
test = r'''
#include "wr-band-settings-snapshot.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static int live_reads, live_status=1, live_config=-40;
static char live[]="changed";
static char *nvram_wlan_get(int band,const char *name)
{ assert((band==0||band==1) && name);++live_reads;return live; }
static int nvram_get_int(const char *name)
{ ++live_reads;return !strcmp(name,"mlme_radio_rt")||!strcmp(name,"mlme_radio_wl")?live_status:live_config; }
__HELPER__
static int reader(char *data,int capacity,int temporary)
{
 const char dump[]="rt_auth_mode=psk\0wl_mode_x=0\0rt_guest_enable=1\0rt_KickStaRssiLow=-75\0inic_disable=0\0mlme_radio_rt=1\0mlme_radio_wl=1\0";
 assert(capacity==256 && temporary==1);memcpy(data,dump,sizeof(dump));return 0;
}
int main(void)
{
 struct wr_band_settings_snapshot s={0};
 char before[256];int previous;
 assert(!strcmp(wr_radio_wlan_get(0,"auth_mode"),"changed"));
 assert(wr_radio_get_int("rt_KickStaRssiLow")==-40);
 assert(!wr_band_snapshot_capture(&s,256,reader));memcpy(before,s.data,sizeof(before));
 wr_radio_snapshot=&s;previous=live_reads;
 assert(!strcmp(wr_radio_wlan_get(0,"auth_mode"),"psk"));
 assert(wr_radio_wlan_get_int(1,"mode_x")==0);
 assert(wr_radio_wlan_get_int(0,"guest_enable")==1);
 assert(!strcmp(wr_radio_wlan_get(1,"missing"),""));
 assert(wr_radio_get_int("rt_KickStaRssiLow")==-75);
 assert(wr_radio_get_int("inic_disable")==0 && wr_radio_get_int("missing")==0);
 assert(live_reads==previous);
 assert(wr_radio_get_int("mlme_radio_rt")==1);
 live_status=0;
 assert(wr_radio_get_int("mlme_radio_rt")==0 && wr_radio_get_int("mlme_radio_wl")==0);
 assert(live_reads==previous+3 && !memcmp(before,s.data,sizeof(before)));
 wr_radio_snapshot=NULL;wr_band_snapshot_release(&s);
 assert(!strcmp(wr_radio_wlan_get(0,"auth_mode"),"changed"));
 assert(wr_radio_get_int("rt_KickStaRssiLow")==-40);
 puts("PASS actual radio settings adapters: captured configuration, live mlme status, missing defaults and ordinary fallback; hardware unverified");
 return 0;
}
'''
a.output.mkdir(parents=True, exist_ok=True)
(a.output / 'radio-snapshot-check.c').write_text(test.replace('__HELPER__', helper))
for name in ['wr-band-settings-snapshot.c', 'wr-band-settings-snapshot.h']:
    (a.output / name).write_bytes((rc / name).read_bytes())
