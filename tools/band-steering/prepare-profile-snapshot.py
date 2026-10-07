#!/usr/bin/env python3
"""Bind the isolated rc profile generator to a caller-owned settings capture.

Apply after prepare-profile-integration.py. This does not capture NVRAM or
activate the production candidate: the Wi-Fi transaction must bind/release a
complete capture around validation and both writes.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
rc = root / 'trunk/user/rc'
path = rc / 'ralink.c'
text = path.read_text()
make_path = rc / 'Makefile'
make = make_path.read_text()
header = rc / 'wr-band-profile-io.h'
declarations = header.read_text()
anchor = '#include "rc.h"\n'
if (text.count(anchor) != 1 or 'wr_profile_snapshot' in text or
        text.count('int wr_band_generate_profiles(int enabled)') != 1 or
        make.count('OBJS += wr-band-profile-policy.o\n') != 1 or
        declarations.count('int wr_band_generate_profiles(int enabled);') != 1):
    raise ValueError('Prepared profile anchors changed; no files written')
if (text.count('nvram_wlan_set(is_aband, "key_type", "1");') != 1 or
        text.count('nvram_wlan_set(is_aband, "key_type", "0");') != 1):
    raise ValueError('Audited derived key_type writes changed; no files written')

# Rewrite existing call sites before inserting the wrappers, whose fallback
# calls must continue to invoke the real shared helpers.
counts = {}
for old, new in [('nvram_safe_get', 'wr_profile_safe_get'),
                 ('nvram_wlan_get', 'wr_profile_wlan_get'),
                 ('nvram_wlan_get_int', 'wr_profile_wlan_get_int'),
                 ('nvram_wlan_set', 'wr_profile_wlan_set')]:
    text, counts[old] = re.subn(r'\b' + old + r'(?=\s*\()', new, text)
    if not counts[old]:
        raise ValueError('Missing audited read/write API: ' + old)
if counts['nvram_wlan_set'] != 2:
    raise ValueError('Unexpected profile NVRAM writes; no files written')

helper = r'''
#ifdef USE_WR_BAND_STEERING_PROFILE
#include "wr-band-settings-snapshot.h"
static const struct wr_band_settings_snapshot *wr_profile_snapshot;
int wr_band_profile_bind_snapshot(const struct wr_band_settings_snapshot *s)
{
    if (wr_profile_snapshot || !s || !s->data || s->capacity < 2) return -1;
    wr_profile_snapshot = s;
    return 0;
}
void wr_band_profile_unbind_snapshot(void)
{
    wr_profile_snapshot = NULL;
}
static char *wr_profile_safe_get(const char *name)
{
    const char *value;
    if (!wr_profile_snapshot) return nvram_safe_get(name);
    value = wr_band_snapshot_get(wr_profile_snapshot, name);
    return (char *)(value ? value : "");
}
static char *wr_profile_wlan_get(int band, const char *name)
{
    const char *value;
    if (!wr_profile_snapshot) return nvram_wlan_get(band, name);
    if (!strcmp(name, "key_type"))
        value = wr_band_snapshot_wlan_key_type(wr_profile_snapshot, band);
    else
        value = wr_band_snapshot_wlan_get(wr_profile_snapshot, band, name);
    /* Legacy generator uses char pointers but does not modify these values. */
    return (char *)(value ? value : "");
}
static int wr_profile_wlan_get_int(int band, const char *name)
{
    return atoi(wr_profile_wlan_get(band, name));
}
static void wr_profile_wlan_set(int band, const char *name, char *value)
{
    /* Both audited writes derive key_type. Bound reads derive it locally,
     * preserving original live writes only outside a captured transaction. */
    if (!wr_profile_snapshot) nvram_wlan_set(band, name, value);
}
#else
#define wr_profile_safe_get nvram_safe_get
#define wr_profile_wlan_get nvram_wlan_get
#define wr_profile_wlan_get_int nvram_wlan_get_int
#define wr_profile_wlan_set nvram_wlan_set
#endif
'''
text = text.replace(anchor, anchor + helper)
make = make.replace('OBJS += wr-band-profile-policy.o\n',
                    'OBJS += wr-band-profile-policy.o wr-band-settings-snapshot.o\n')
declarations = declarations.replace('int wr_band_generate_profiles(int enabled);',
    'struct wr_band_settings_snapshot;\n'
    '/* Capture must remain valid and immutable until unbound. Caller serializes\n'
    ' * binding, validation and both writes. Bind does not acquire the capture. */\n'
    'int wr_band_profile_bind_snapshot(const struct wr_band_settings_snapshot *);\n'
    'void wr_band_profile_unbind_snapshot(void);\n'
    'int wr_band_generate_profiles(int enabled);')
module = Path(__file__).parent
files = {
    path: text.encode(), make_path: make.encode(), header: declarations.encode(),
    rc / 'wr-band-settings-snapshot.c': (module / 'settings-snapshot.c').read_bytes().replace(
        b'"settings-snapshot.h"', b'"wr-band-settings-snapshot.h"'),
    rc / 'wr-band-settings-snapshot.h': (module / 'settings-snapshot.h').read_bytes(),
}
report = {'runtime_verified': False, 'transaction_binding_complete': False,
          'rewritten_calls': counts, 'files': []}
for file, data in files.items():
    before = file.read_bytes() if file.exists() else b''
    report['files'].append({'path': file.relative_to(root).as_posix(),
        'before_sha256': hashlib.sha256(before).hexdigest(),
        'after_sha256': hashlib.sha256(data).hexdigest()})
for file, data in files.items():
    file.write_bytes(data)
(root / 'band-steering-profile-snapshot.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
