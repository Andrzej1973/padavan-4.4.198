#!/usr/bin/env python3
"""Add a read-only rc observation event; not a current driver-state proof."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
rc = p.parse_args().source / 'trunk/user/rc'
wifi, dispatch, header = (rc/name for name in ('net_wifi.c', 'rc.c', 'wr-band-wifi-lifecycle.h'))
w, d, h = (path.read_text(encoding='utf-8') for path in (wifi, dispatch, header))
anchor = '        else if (!strcmp(entry->d_name, "restart_wr_band_steering"))\n'
if (d.count(anchor) != 1 or 'wr_band_wifi_observe_status' in w or
    w.count('static struct wr_band_service_owner wr_wifi_owner;') != 1 or
    h.count('#endif') != 1):
    raise ValueError('Status observation source anchors changed; no files written')
function = r'''
#ifdef USE_WR_BAND_STEERING_PROFILE
#include "wr-band-control-client.h"
#include <limits.h>
static unsigned int wr_bs_observation_serial;
/* 0: unknown, 1: authenticated daemon reports ACTIVE, 2: last verified OFF.
 * A saved PID or missing socket never proves ACTIVE or OFF. */
void wr_band_wifi_observe_status(void)
{
    int observed = 0;
    wr_band_wifi_refresh_exit_status();
    if (nvram_get_int("wr_bs_off_confirmed") == 1 &&
        nvram_get_int("wr_bs_apply_state") == WR_APPLY_OFF_CONFIRMED)
        observed = 2;
    else if (wr_wifi_owner.pid > 1 && !wr_band_control_active(wr_wifi_owner.pid))
        observed = 1;
    if (wr_bs_observation_serial >= INT_MAX)
        wr_bs_observation_serial = 0;
    ++wr_bs_observation_serial;
    nvram_set_int_temp("wr_bs_observation", observed);
    nvram_set_int_temp("wr_bs_observation_serial", (int)wr_bs_observation_serial);
}
#endif
'''
w += function
d = d.replace(anchor,
    '        else if (!strcmp(entry->d_name, "observe_wr_band_steering"))\n'
    '            wr_band_wifi_observe_status();\n'+anchor)
h = h.replace('#endif', 'void wr_band_wifi_observe_status(void);\n#endif')
for path, text in ((wifi, w), (dispatch, d), (header, h)):
    path.write_text(text, encoding='utf-8')
print('Added rc observation: authenticated ACTIVE or last verified OFF; no Wi-Fi restart')
