#!/usr/bin/env python3
"""Extract the installed rc profile helper for host and target compilation checks."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
rc = a.source / 'trunk/user/rc'
s = (rc / 'ralink.c').read_text()
start = s.index('static int wr_band_profile_override = -1;')
helper = s[start:s.index('\n#endif', start)]
paired_start = s.index('int wr_band_generate_profiles(int enabled)')
paired = s[paired_start:s.index('\n#endif', paired_start)]
test = r'''
#include "wr-band-profile-policy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int requested, mismatched, reads;
static int nvram_match(const char *name, const char *value) {
    assert(!strcmp(name, "wr_bs_enable") && !strcmp(value, "1")); return requested;
}
static const char *nvram_wlan_get(int band, const char *name) {
    static char reused[80]; const char *value = "0"; ++reads;
    if (!strcmp(name, "ssid")) value = band && mismatched ? "other" : "same";
    else if (!strcmp(name, "auth_mode")) value = "psk";
    else if (!strcmp(name, "crypto")) value = "aes";
    else if (!strcmp(name, "wpa_psk")) value = "abcdefgh";
    else if (!strcmp(name, "radio_x")) value = "1";
    else if (!strcmp(name, "wpa_mode")) value = "2";
    strcpy(reused, value); return reused;
}
__HELPER__
static int writes2g, writes5g, fail_band, expected_mode;
static int gen_ralink_config_2g(int scan) {
    assert(!scan && wr_band_profile_override == expected_mode); ++writes2g;
    return fail_band == 2 ? -1 : 0;
}
static int gen_ralink_config_5g(int scan) {
    assert(!scan && wr_band_profile_override == expected_mode); ++writes5g;
    return fail_band == 5 ? -1 : 0;
}
__PAIRED__
static void check(int band, int count, const char *expected) {
    FILE *f = tmpfile(); char out[128]; size_t n;
    assert(f); wr_band_write_profile(f, band, count); assert(!fflush(f)); rewind(f);
    n = fread(out, 1, sizeof(out) - 1, f); out[n] = 0;
    assert(!ferror(f) && !strcmp(out, expected)); assert(!fclose(f));
}
int main(void) {
    check(0, 2, "BandSteering=0\nBndStrgBssIdx=0;0\n"); assert(!reads);
    requested = 1;
    check(0, 2, "BandSteering=1\nBndStrgBssIdx=1;0\n");
    check(0, 4, "BandSteering=1\nBndStrgBssIdx=1;0;0;0\n");
    check(1, 2, "BandSteering=1\n");
    mismatched = 1;
    check(0, 2, "BandSteering=0\nBndStrgBssIdx=0;0\n");
    check(1, 2, "BandSteering=0\n");
    /* Exercise the actual extracted paired function with failed writes. */
    mismatched = 0; expected_mode = 0;
    assert(!wr_band_generate_profiles(0) && writes2g == 1 && writes5g == 1);
    assert(wr_band_profile_override == -1 && requested == 1);
    expected_mode = 1; fail_band = 2;
    assert(wr_band_generate_profiles(1) == -1 && writes2g == 2 && writes5g == 1);
    assert(wr_band_profile_override == -1);
    fail_band = 5;
    assert(wr_band_generate_profiles(1) == -1 && writes2g == 3 && writes5g == 2);
    assert(wr_band_profile_override == -1);
    fail_band = 0;
    assert(!wr_band_generate_profiles(1) && writes2g == 4 && writes5g == 3);
    assert(wr_band_profile_override == -1);
    mismatched = 1;
    assert(wr_band_generate_profiles(1) == -1 && writes2g == 4 && writes5g == 3);
    assert(wr_band_generate_profiles(2) == -1 && wr_band_profile_override == -1);
    puts("PASS actual rc profile helper: factory off, matching credentials, guest exclusion and mismatch off");
    return 0;
}
'''
a.output.mkdir(parents=True, exist_ok=True)
(a.output / 'profile-integration-check.c').write_text(test.replace('__HELPER__', helper).replace('__PAIRED__', paired))
for n in ('wr-band-profile-policy.c', 'wr-band-profile-policy.h'):
    (a.output / n).write_bytes((rc / n).read_bytes())

