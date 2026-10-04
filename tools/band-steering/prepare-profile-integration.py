#!/usr/bin/env python3
"""Connect candidate compatibility policy to rc profile generation behind a build gate."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
rc = root / 'trunk/user/rc'
source = rc / 'ralink.c'
makefile = rc / 'Makefile'
text = source.read_text()
make = makefile.read_text()
include = '#include "rc.h"\n'
old = '\n\tfprintf(fp, "BandSteering=%d\\n", 0);\n'
if text.count(include) != 1 or text.count(old) != 1 or 'wr_band_write_profile' in text:
    raise ValueError('Profile anchors changed; no files written')
if make.count('all: $(OBJS) Makefile\n') != 1 or 'wr-band-profile-policy.o' in make:
    raise ValueError('rc build anchors changed; no files written')
policy = {name: (Path(__file__).parent / name).read_bytes()
          for name in ('profile-policy.c', 'profile-policy.h')}
helper = r'''
#ifdef USE_WR_BAND_STEERING_PROFILE
#include "wr-band-profile-policy.h"
#if !defined(USE_WID_2G) || USE_WID_2G != 7603 || !defined(USE_WID_5G) || USE_WID_5G != 7612
#error "WR Band Steering profile candidate requires MT7603E plus MT7612E"
#endif
static const char *wr_band_profile_setting(int band, const char *name, void *context)
{
    (void)context;
    return nvram_wlan_get(band, name);
}
static void wr_band_write_profile(FILE *fp, int is_aband, int ssid_count)
{
    int i;
    int enabled = wr_band_profile_from_settings(
        nvram_match("wr_bs_enable", "1"), wr_band_profile_setting, NULL) == WR_PROFILE_COMPATIBLE;
    fprintf(fp, "BandSteering=%d\n", enabled);
    if (!is_aband) {
        /* Explicitly exclude every guest BSS from the modern driver. */
        fprintf(fp, "BndStrgBssIdx=");
        for (i = 0; i < ssid_count; ++i)
            fprintf(fp, "%s%d", i ? ";" : "", i == 0 && enabled);
        fprintf(fp, "\n");
    }
}
#endif
'''
new_text = text.replace(include, include + helper).replace(old,
    '\n#ifdef USE_WR_BAND_STEERING_PROFILE\n'
    '\twr_band_write_profile(fp, is_aband, i_ssid_num);\n'
    '#else' + old + '#endif\n')
gate = '''ifeq ($(CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING),y)
CFLAGS += -DUSE_WR_BAND_STEERING_PROFILE
OBJS += wr-band-profile-policy.o
endif

'''
# Place the addition after the base OBJS assignment, which otherwise overwrites it.
new_make = make.replace('all: $(OBJS) Makefile\n', gate + 'all: $(OBJS) Makefile\n')
report = {'runtime_verified': False, 'enabled_by_default': False, 'files': []}
for path, data in [(source, new_text.encode()), (makefile, new_make.encode()),
                   (rc / 'wr-band-profile-policy.c', policy['profile-policy.c'].replace(
                       b'"profile-policy.h"', b'"wr-band-profile-policy.h"')),
                   (rc / 'wr-band-profile-policy.h', policy['profile-policy.h'])]:
    before = path.read_bytes() if path.exists() else b''
    path.write_bytes(data)
    report['files'].append({'path': path.relative_to(root).as_posix(),
        'before_sha256': hashlib.sha256(before).hexdigest(),
        'after_sha256': hashlib.sha256(data).hexdigest()})
(root / 'band-steering-profile-integration.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

