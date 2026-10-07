"""Bind candidate lifecycle callbacks to actual rc Wi-Fi routines, isolated only."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument('source', type=Path)
rc = p.parse_args().source / 'trunk/user/rc'
path = rc / 'net_wifi.c'; text = path.read_text()
dispatch_path = rc / 'rc.c'; dispatch = dispatch_path.read_text()
anchor = '\t\telse if (!strcmp(entry->d_name, RCN_RESTART_WIFI5))\n'
if dispatch.count(anchor) != 1 or dispatch.count('#include "rc.h"\n') != 1:
    raise ValueError('rc event anchors changed; no files written')
event = r'''#ifdef USE_WR_BAND_STEERING_PROFILE
        else if (!strcmp(entry->d_name, "restart_wr_band_steering"))
        {
            struct wr_band_apply_result result;
            int radio2g = get_enabled_radio_rt();
            int radio5g = get_enabled_radio_wl();
            int status;
            if (radio2g) radio2g = is_radio_allowed_rt();
            if (radio5g) radio5g = is_radio_allowed_wl();
            status = wr_band_apply_wifi_settings(nvram_match("wr_bs_enable", "1"),
                                                 !!radio2g, !!radio5g, &result);
            nvram_set_int_temp("wr_bs_apply_state", result.state);
            nvram_set_int_temp("wr_bs_off_confirmed", result.off_confirmed);
            if (status)
                logmessage("Band Steering", "Apply failed: state=%d off_confirmed=%d",
                           result.state, result.off_confirmed);
        }
#endif
'''
dispatch = dispatch.replace('#include "rc.h"\n', '#include "rc.h"\n#ifdef USE_WR_BAND_STEERING_PROFILE\n#include "wr-band-wifi-lifecycle.h"\n#endif\n').replace(anchor, event + anchor)
if text.count('#include "rc.h"\n') != 1 or 'wr_band_apply_wifi_settings' in text:
    raise ValueError('Wi-Fi integration anchor changed; no files written')
for name in ['wr-band-profile-io.h', 'wr-band-service-owner.h']:
    if not (rc / name).is_file():
        raise ValueError('Prepare profile and child integration first')
helper = r'''
#ifdef USE_WR_BAND_STEERING_PROFILE
#include "wr-band-profile-io.h"
#include "wr-band-service-owner.h"
#include "wr-band-profile-policy.h"
static struct wr_band_service_owner wr_wifi_owner;
static int wr_wifi_applying;
struct wr_wifi_apply_context { int radio2g, radio5g; };
static const char *wr_wifi_setting(int band, const char *name, void *context)
{
    (void)context;
    return nvram_wlan_get(band, name);
}
static int wr_wifi_validate(void *p)
{
    struct wr_wifi_apply_context *c = p;
    if (!c->radio2g || !c->radio5g) return -1;
    /* Reject incompatible credentials before stopping a running service. */
    return wr_band_profile_from_settings(1, wr_wifi_setting, NULL) == WR_PROFILE_COMPATIBLE ? 0 : -1;
}
static int wr_wifi_profiles(void *p, int enabled)
{
    (void)p;
    if (wr_band_generate_profiles(enabled)) return -1;
    nvram_set_int_temp("reload_svc_rt", 1);
    nvram_set_int_temp("reload_svc_wl", 1);
    return 0;
}
static int wr_wifi_initialize(void *p)
{
    struct wr_wifi_apply_context *c = p;
    /* Profiles already written. Keep the existing AP/WDS/APCLI/802.1x,
     * guest isolation, WAN, LED and iappd actions of both restart routines. */
    restart_wifi_rt(c->radio2g, 0);
    restart_wifi_wl(c->radio5g, 0);
    if (c->radio2g && !is_interface_up(IFNAME_2G_MAIN)) return -1;
    if (c->radio5g && !is_interface_up(IFNAME_5G_MAIN)) return -1;
    return 0;
}
/* rc caller must serialize settings across the whole call and provide actual
 * scheduled radio states. This endpoint is not yet dispatched by rc events. */
int wr_band_apply_wifi_settings(int enabled, int radio2g, int radio5g,
                               struct wr_band_apply_result *result)
{
    struct wr_wifi_apply_context context = {radio2g, radio5g};
    struct wr_band_lifecycle_ops ops = {wr_wifi_validate, NULL,
        wr_wifi_profiles, wr_wifi_initialize, NULL};
    int status;
    if (wr_wifi_applying || (radio2g != 0 && radio2g != 1) ||
        (radio5g != 0 && radio5g != 1)) {
        if (result) { result->state = WR_APPLY_REJECTED; result->off_confirmed = 0; }
        return -1;
    }
    wr_wifi_applying = 1;
    status = wr_band_service_apply(&wr_wifi_owner, IFNAME_2G_MAIN, IFNAME_5G_MAIN,
                                  &ops, &context, enabled, result);
    wr_wifi_applying = 0;
    return status;
}
#endif
'''
path.write_text(text + helper)
dispatch_path.write_text(dispatch)
(rc / 'wr-band-wifi-lifecycle.h').write_text('''#ifndef WR_BAND_WIFI_LIFECYCLE_H
#define WR_BAND_WIFI_LIFECYCLE_H
#include "wr-band-lifecycle.h"
/* rc caller serializes NVRAM updates and supplies actual scheduled states.
 * No event dispatcher or WebUI integration is installed by this header. */
int wr_band_apply_wifi_settings(int enabled, int radio2g, int radio5g,
                               struct wr_band_apply_result *result);
#endif
''')
print('Paired rc callbacks and dedicated steering apply event installed; global settings serialization pending')
