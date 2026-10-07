"""Bind candidate lifecycle callbacks to actual rc Wi-Fi routines, isolated only."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument('source', type=Path)
rc = p.parse_args().source / 'trunk/user/rc'
path = rc / 'net_wifi.c'; text = path.read_text()
init_path = rc / 'init.c'; init = init_path.read_text()
reaped = '\t\twr_band_child_reaped(pid, status);\n'
if init.count(reaped) != 1 or init.count('#include "wr-band-child-owner.h"\n') != 1:
    raise ValueError('Owned child reaper anchor changed; no files written')
init = init.replace('#include "wr-band-child-owner.h"\n',
    '#include "wr-band-child-owner.h"\n#include "wr-band-wifi-lifecycle.h"\n').replace(reaped,
    reaped + '\t\twr_band_wifi_child_exit(pid, status);\n')
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
shutdown_anchor = '\tstop_8021x_all();\n\tstop_wifi_all_wl();\n\tstop_wifi_all_rt();\n'
if dispatch.count(shutdown_anchor) != 1:
    raise ValueError('Shutdown ordering anchor changed; no files written')
dispatch = dispatch.replace(shutdown_anchor,
    '#ifdef USE_WR_BAND_STEERING_PROFILE\n\twr_band_wifi_shutdown();\n#endif\n' + shutdown_anchor)
boot_anchor = '\tgen_ralink_config_2g(0);\n\tgen_ralink_config_5g(0);\n\tload_wireless_modules();\n'
ready_anchor = '\tstart_services_once(is_ap_mode);\n'
if dispatch.count(boot_anchor) != 1 or dispatch.count(ready_anchor) != 1:
    raise ValueError('Boot Wi-Fi ordering anchors changed; no files written')
boot = '''#ifdef USE_WR_BAND_STEERING_PROFILE
\tnvram_set_int_temp("wr_bs_boot_profiles_ready", 0);
\tif (!wr_band_generate_profiles(0)) {
\t\tload_wireless_modules();
\t\tnvram_set_int_temp("wr_bs_boot_profiles_ready", 1);
\t} else {
\t\tlogmessage("Band Steering", "Boot profile write failed; wireless modules not loaded");
\t}
#else
''' + boot_anchor + '#endif\n'
dispatch = dispatch.replace(boot_anchor, boot).replace(ready_anchor,
    ready_anchor + '#ifdef USE_WR_BAND_STEERING_PROFILE\n\twr_band_wifi_startup();\n#endif\n')
dispatch = dispatch.replace('#include "wr-band-wifi-lifecycle.h"\n',
    '#include "wr-band-wifi-lifecycle.h"\n#include "wr-band-profile-io.h"\n')
notify_anchor = '\tDIR *directory = opendir(DIR_RC_NOTIFY);\n'
if dispatch.count(notify_anchor) != 1:
    raise ValueError('Notification context anchor changed; no files written')
dispatch = dispatch.replace(notify_anchor, notify_anchor +
    '#ifdef USE_WR_BAND_STEERING_PROFILE\n\twr_band_wifi_refresh_exit_status();\n#endif\n')
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
#include <sys/wait.h>
#include <signal.h>
static struct wr_band_service_owner wr_wifi_owner;
static int wr_wifi_applying;
static int wr_wifi_last_status;
static volatile sig_atomic_t wr_wifi_exit_pending;
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
int wr_band_handle_wifi_restart(int band, int radio_on)
{
    struct wr_band_apply_result result;
    int radio2g, radio5g, enabled, status;
    if (wr_wifi_applying || (!wr_wifi_owner.pid && !nvram_match("wr_bs_enable", "1")))
        return 0;
    radio2g = get_enabled_radio_rt();
    radio5g = get_enabled_radio_wl();
    if (radio2g) radio2g = is_radio_allowed_rt();
    if (radio5g) radio5g = is_radio_allowed_wl();
    if (band) radio5g = radio_on; else radio2g = radio_on;
    enabled = nvram_match("wr_bs_enable", "1") && radio2g && radio5g &&
        wr_band_profile_from_settings(1, wr_wifi_setting, NULL) == WR_PROFILE_COMPATIBLE;
    /* Incompatible settings/radio schedules disable steering, preserving the
     * user's new Wi-Fi settings and persistent requested enable flag. */
    status = wr_band_apply_wifi_settings(enabled, !!radio2g, !!radio5g, &result);
    wr_wifi_last_status = status;
    nvram_set_int_temp("wr_bs_apply_state", result.state);
    nvram_set_int_temp("wr_bs_off_confirmed", result.off_confirmed);
    if (status)
        logmessage("Band Steering", "Wi-Fi restart failed: state=%d off_confirmed=%d",
                   result.state, result.off_confirmed);
    /* Never bypass failed OFF proof with an ordinary uncoordinated restart. */
    return 1;
}
int wr_band_wifi_shutdown(void)
{
    int status;
    /* No work when steering has never been requested or owned. This is not
     * a driver OFF observation and does not publish OFF confirmation. */
    if (!wr_wifi_owner.pid && !nvram_match("wr_bs_enable", "1")) return 0;
    status = wr_band_service_quiesce(&wr_wifi_owner, IFNAME_2G_MAIN, IFNAME_5G_MAIN);
    nvram_set_int_temp("wr_bs_apply_state", status ? WR_APPLY_OFF_UNVERIFIED : WR_APPLY_OFF_CONFIRMED);
    nvram_set_int_temp("wr_bs_off_confirmed", !status);
    if (status)
        logmessage("Band Steering", "Shutdown OFF acknowledgement unverified");
    return status;
}
void wr_band_wifi_child_exit(pid_t pid, int status)
{
    if (pid != wr_wifi_owner.pid || pid <= 1) return;
    /* SIGCHLD path: no NVRAM, allocation or logging from the handler. */
    wr_wifi_exit_pending = WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 1 : 2;
}
void wr_band_wifi_refresh_exit_status(void)
{
    sigset_t mask, previous;
    int pending, confirmed;
    sigemptyset(&mask); sigaddset(&mask, SIGCHLD);
    if (sigprocmask(SIG_BLOCK, &mask, &previous)) return;
    pending = wr_wifi_exit_pending; wr_wifi_exit_pending = 0;
    if (sigprocmask(SIG_SETMASK, &previous, NULL)) return;
    if (!pending) return;
    confirmed = pending == 1;
    nvram_set_int_temp("wr_bs_apply_state", confirmed ? WR_APPLY_OFF_CONFIRMED : WR_APPLY_OFF_UNVERIFIED);
    nvram_set_int_temp("wr_bs_off_confirmed", confirmed);
    /* Keep ownership until child-owner consumes the cached wait status. */
}
int wr_band_wifi_startup(void)
{
    int radio2g;
    if (!nvram_match("wr_bs_enable", "1")) return 0;
    if (!nvram_match("wr_bs_boot_profiles_ready", "1")) {
        nvram_set_int_temp("wr_bs_apply_state", WR_APPLY_PROFILE_ERROR);
        nvram_set_int_temp("wr_bs_off_confirmed", 0);
        return -1;
    }
    radio2g = get_enabled_radio_rt();
    if (radio2g) radio2g = is_radio_allowed_rt();
    return wr_band_handle_wifi_restart(0, !!radio2g) ? wr_wifi_last_status : -1;
}
#endif
'''
for name, band in [('restart_wifi_rt', 0), ('restart_wifi_wl', 1)]:
    anchor = 'void\n%s(int radio_on, int need_reload_conf)\n{\n' % name
    if text.count(anchor) != 1:
        raise ValueError('Radio restart entry changed; no files written')
    text = text.replace(anchor, anchor + '#ifdef USE_WR_BAND_STEERING_PROFILE\n'
        '\tif (wr_band_handle_wifi_restart(%d, radio_on)) return;\n' % band + '#endif\n')
text = text.replace('#include "rc.h"\n', '#include "rc.h"\n#ifdef USE_WR_BAND_STEERING_PROFILE\n#include "wr-band-wifi-lifecycle.h"\n#endif\n')
path.write_text(text + helper)
dispatch_path.write_text(dispatch)
init_path.write_text(init)
(rc / 'wr-band-wifi-lifecycle.h').write_text('''#ifndef WR_BAND_WIFI_LIFECYCLE_H
#define WR_BAND_WIFI_LIFECYCLE_H
#include "wr-band-lifecycle.h"
#include <sys/types.h>
/* rc caller serializes NVRAM updates and supplies actual scheduled states.
 * No event dispatcher or WebUI integration is installed by this header. */
int wr_band_apply_wifi_settings(int enabled, int radio2g, int radio5g,
                               struct wr_band_apply_result *result);
int wr_band_handle_wifi_restart(int band, int radio_on);
int wr_band_wifi_shutdown(void);
int wr_band_wifi_startup(void);
void wr_band_wifi_child_exit(pid_t pid, int status);
/* Call from normal rc/WebUI status handling, never from a signal handler. */
void wr_band_wifi_refresh_exit_status(void);
#endif
''')
print('Paired rc callbacks and dedicated steering apply event installed; global settings serialization pending')
