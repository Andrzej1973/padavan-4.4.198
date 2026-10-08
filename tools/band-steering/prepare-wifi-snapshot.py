#!/usr/bin/env python3
"""Use one real NVRAM capture for candidate policy and paired profile writes.

Apply after Wi-Fi lifecycle and profile snapshot preparation. Requires the
candidate kernel's overflow-reporting NVRAM getall. Radio initialization and
user AP.dat additions are not made immutable by this adapter.
"""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
rc = p.parse_args().source / 'trunk/user/rc'
path = rc / 'net_wifi.c'
text = path.read_text()
if not (rc / 'wr-band-settings-snapshot.h').is_file():
    raise ValueError('Prepare profile snapshot first')
replacements = {
    '#include "wr-band-profile-policy.h"\n':
        '#include "wr-band-profile-policy.h"\n#include "wr-band-settings-snapshot.h"\n',
    'struct wr_wifi_apply_context { int radio2g, radio5g; };':
        'struct wr_wifi_apply_context { int radio2g, radio5g;\n'
        '    const struct wr_band_settings_snapshot *snapshot; };',
    '''    (void)context;
    return nvram_wlan_get(band, name);''':
        '''    struct wr_wifi_apply_context *c = context;
    const char *value;
    if (!c) return nvram_wlan_get(band, name);
    value = wr_band_snapshot_wlan_get(c->snapshot, band, name);
    return value ? value : "";''',
    'wr_band_profile_from_settings(1, wr_wifi_setting, NULL) == WR_PROFILE_COMPATIBLE ? 0 : -1;':
        'wr_band_profile_from_settings(1, wr_wifi_setting, c) == WR_PROFILE_COMPATIBLE ? 0 : -1;',
    '    struct wr_wifi_apply_context context = {radio2g, radio5g};':
        '    struct wr_band_settings_snapshot snapshot = {0};\n'
        '    struct wr_wifi_apply_context context = {radio2g, radio5g, &snapshot};',
    '''    wr_wifi_applying = 1;
    status = wr_band_service_apply(&wr_wifi_owner, IFNAME_2G_MAIN, IFNAME_5G_MAIN,
                                  &ops, &context, enabled, result);
    wr_wifi_applying = 0;
    return status;''':
        '''    wr_wifi_applying = 1;
    /* Largest allocation in the pinned NVRAM header is 128 KiB (NAND).
     * Supplying that capacity also covers WR1200JS NOR's 60 KiB dump.
     * Kernel getall must return an error rather than a truncated success. */
    if (wr_band_snapshot_capture(&snapshot, 0x20000, nvram_getall)) {
        if (result) { result->state = WR_APPLY_REJECTED; result->off_confirmed = 0; }
        wr_wifi_applying = 0;
        return -1;
    }
    if (wr_band_profile_bind_snapshot(&snapshot)) {
        wr_band_snapshot_release(&snapshot);
        if (result) { result->state = WR_APPLY_REJECTED; result->off_confirmed = 0; }
        wr_wifi_applying = 0;
        return -1;
    }
    status = wr_band_service_apply(&wr_wifi_owner, IFNAME_2G_MAIN, IFNAME_5G_MAIN,
                                  &ops, &context, enabled, result);
    /* Unbind before wiping the capture; every service failure follows this
     * cleanup path. Neither validation nor both writes read live NVRAM. */
    wr_band_profile_unbind_snapshot();
    wr_band_snapshot_release(&snapshot);
    wr_wifi_applying = 0;
    return status;''',
}
for old in replacements:
    if text.count(old) != 1:
        raise ValueError('Wi-Fi snapshot anchor changed; no files written: ' + old[:70])
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
print('Prepared actual NVRAM capture, shared validation/profile snapshot and cleanup; radio initialization/runtime verification pending')
