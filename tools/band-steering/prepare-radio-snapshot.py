#!/usr/bin/env python3
"""Redirect original net_wifi settings reads during coordinated apply only.

Apply after prepare-wifi-snapshot.py. Live mlme radio status must remain live;
external programs/files and other translation units are outside this adapter.
"""
import argparse
import re
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
path = p.parse_args().source / 'trunk/user/rc/net_wifi.c'
text = path.read_text()
marker = '#ifdef USE_WR_BAND_STEERING_PROFILE\n#include "wr-band-profile-io.h"'
anchor = '#include "rc.h"\n'
if text.count(marker)!=1 or text.count(anchor)!=1 or 'wr_radio_snapshot' in text:
    raise ValueError('Radio snapshot source anchors changed; no files written')
prefix, suffix = text.split(marker)
counts = {}
for old,new in [('nvram_wlan_get','wr_radio_wlan_get'),
                ('nvram_wlan_get_int','wr_radio_wlan_get_int'),
                ('nvram_get_int','wr_radio_get_int')]:
    prefix, counts[old] = re.subn(r'\b'+old+r'(?=\s*\()',new,prefix)
expected_counts = {'nvram_wlan_get': 10, 'nvram_wlan_get_int': 22,
                   'nvram_get_int': 8}
if counts != expected_counts:
    raise ValueError('Audited radio read counts changed; no files written: '+str(counts))
reads = set(re.findall(r'wr_radio_get_int\("([^"]+)"\)', prefix))
if reads != {'mlme_radio_wl','mlme_radio_rt','inic_disable','wl_KickStaRssiLow',
             'wl_AssocReqRssiThres','rt_KickStaRssiLow','rt_AssocReqRssiThres'}:
    raise ValueError('Radio global settings/status key set changed; no files written')
helper = r'''
#ifdef USE_WR_BAND_STEERING_PROFILE
#include "wr-band-settings-snapshot.h"
static const struct wr_band_settings_snapshot *wr_radio_snapshot;
static char *wr_radio_wlan_get(int band, const char *name)
{
    const char *value;
    if (!wr_radio_snapshot) return nvram_wlan_get(band, name);
    value = wr_band_snapshot_wlan_get(wr_radio_snapshot, band, name);
    return (char *)(value ? value : "");
}
static int wr_radio_wlan_get_int(int band, const char *name)
{
    return atoi(wr_radio_wlan_get(band, name));
}
static int wr_radio_get_int(const char *name)
{
    const char *value;
    /* Driver status changes during restart; a captured status would be stale. */
    if (!wr_radio_snapshot || !strcmp(name,"mlme_radio_wl") ||
        !strcmp(name,"mlme_radio_rt")) return nvram_get_int(name);
    value = wr_band_snapshot_get(wr_radio_snapshot, name);
    return value ? atoi(value) : 0;
}
#else
#define wr_radio_wlan_get nvram_wlan_get
#define wr_radio_wlan_get_int nvram_wlan_get_int
#define wr_radio_get_int nvram_get_int
#endif
'''
bind = '    status = wr_band_service_apply(&wr_wifi_owner, IFNAME_2G_MAIN, IFNAME_5G_MAIN,'
cleanup = '    wr_band_profile_unbind_snapshot();\n'
if suffix.count(bind)!=1 or suffix.count(cleanup)!=1:
    raise ValueError('Captured transaction lifetime changed; no files written')
suffix = suffix.replace(bind, '    wr_radio_snapshot = &snapshot;\n'+bind)
suffix = suffix.replace(cleanup, '    wr_radio_snapshot = NULL;\n'+cleanup)
prefix = prefix.replace(anchor,anchor+helper)
path.write_text(prefix+marker+suffix)
print('Prepared original radio settings reads from transaction capture; live mlme status retained; counts='+str(counts))

