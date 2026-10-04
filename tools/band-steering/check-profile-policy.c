#include "profile-policy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
    struct wr_band_credentials b[2] = {
        {1, 0, 0, 2, "same", "psk", "aes", "abcdefgh"},
        {1, 0, 0, 2, "same", "psk", "aes", "abcdefgh"}
    };
    char key[66], ssid[34]; int mode;
    assert(wr_band_profile_validate(0, NULL) == WR_PROFILE_DISABLED);
    assert(wr_band_profile_validate(2, b) == WR_PROFILE_INVALID);
    assert(wr_band_profile_validate(1, NULL) == WR_PROFILE_INVALID);
    for (mode = 0; mode <= 2; ++mode) {
        b[0].wpa_mode = b[1].wpa_mode = mode;
        assert(wr_band_profile_validate(1, b) == WR_PROFILE_COMPATIBLE);
    }
    b[1].ssid = "other"; assert(wr_band_profile_validate(1, b) == WR_PROFILE_MISMATCH); b[1].ssid = "same";
    b[1].psk = "different"; assert(wr_band_profile_validate(1, b) == WR_PROFILE_MISMATCH); b[1].psk = "abcdefgh";
    b[1].hidden = 1; assert(wr_band_profile_validate(1, b) == WR_PROFILE_MISMATCH); b[1].hidden = 0;
    b[1].radio_enabled = 0; assert(wr_band_profile_validate(1, b) == WR_PROFILE_RADIO_OFF); b[1].radio_enabled = 1;
    b[1].wep_enabled = 1; assert(wr_band_profile_validate(1, b) == WR_PROFILE_UNSUPPORTED_SECURITY); b[1].wep_enabled = 0;
    b[1].auth_mode = "wpa2"; assert(wr_band_profile_validate(1, b) == WR_PROFILE_UNSUPPORTED_SECURITY); b[1].auth_mode = "psk";
    memset(key, 'a', 64); key[64] = 0; b[0].psk = b[1].psk = key;
    assert(wr_band_profile_validate(1, b) == WR_PROFILE_COMPATIBLE);
    key[63] = 'x'; assert(wr_band_profile_validate(1, b) == WR_PROFILE_INVALID);
    key[63] = 'a'; key[64] = 'a'; key[65] = 0; assert(wr_band_profile_validate(1, b) == WR_PROFILE_INVALID);
    b[0].psk = b[1].psk = "short"; assert(wr_band_profile_validate(1, b) == WR_PROFILE_INVALID);
    b[0].psk = b[1].psk = "abcdefgh";
    memset(ssid, 's', 32); ssid[32] = 0; b[0].ssid = b[1].ssid = ssid;
    assert(wr_band_profile_validate(1, b) == WR_PROFILE_COMPATIBLE);
    ssid[32] = 's'; ssid[33] = 0; assert(wr_band_profile_validate(1, b) == WR_PROFILE_INVALID);
    b[0].ssid = b[1].ssid = "bad\nssid"; assert(wr_band_profile_validate(1, b) == WR_PROFILE_INVALID);
    b[0].ssid = b[1].ssid = "same"; b[0].auth_mode = b[1].auth_mode = "open";
    b[0].psk = b[1].psk = NULL; b[0].crypto = b[1].crypto = NULL;
    assert(wr_band_profile_validate(1, b) == WR_PROFILE_COMPATIBLE);
    puts("PASS read-only profile compatibility and disabled/mismatch/security boundaries");
    return 0;
}

