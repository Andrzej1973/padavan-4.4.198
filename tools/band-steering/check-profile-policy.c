#include "profile-policy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int reads, mismatch, invalid, ap_mode, mode_band;
static const char *setting(int band, const char *name, void *context)
{
    static char reused[80]; const char *value = "0";
    (void)context; ++reads;
    if (!strcmp(name, "ssid")) value = band && mismatch ? "different" : "same";
    else if (!strcmp(name, "auth_mode")) value = "psk";
    else if (!strcmp(name, "crypto")) value = "aes";
    else if (!strcmp(name, "wpa_psk")) value = "abcdefgh";
    else if (!strcmp(name, "radio_x")) value = invalid ? "1junk" : "1";
    else if (!strcmp(name, "wpa_mode")) value = "2";
    else if (!strcmp(name, "mode_x")) {
        static const char *modes[] = {"0","1","2","3","4","5"};
        value = band==mode_band ? modes[ap_mode] : "0";
    }
    strcpy(reused, value); return reused;
}
int main(void)
{
    struct wr_band_credentials b[2] = {
        {1, 0, 0, 2, "same", "psk", "aes", "abcdefgh"},
        {1, 0, 0, 2, "same", "psk", "aes", "abcdefgh"}
    };
    char key[66], ssid[34]; int mode;
    assert(wr_band_profile_from_settings(0, setting, NULL) == WR_PROFILE_DISABLED && !reads);
    assert(wr_band_profile_from_settings(1, NULL, NULL) == WR_PROFILE_INVALID);
    assert(wr_band_profile_from_settings(1, setting, NULL) == WR_PROFILE_COMPATIBLE && reads == 18);
    mismatch = 1; assert(wr_band_profile_from_settings(1, setting, NULL) == WR_PROFILE_MISMATCH);
    mismatch = 0; invalid = 1; assert(wr_band_profile_from_settings(1, setting, NULL) == WR_PROFILE_INVALID);
    invalid = 0;
    for (mode_band=0;mode_band<2;++mode_band) {
        for (ap_mode=0;ap_mode<5;++ap_mode)
            assert(wr_band_profile_from_settings(1,setting,NULL)==
                (ap_mode==1 || ap_mode==3 ? WR_PROFILE_AP_UNAVAILABLE : WR_PROFILE_COMPATIBLE));
        ap_mode=5;
        assert(wr_band_profile_from_settings(1,setting,NULL)==WR_PROFILE_INVALID);
    }
    ap_mode=mode_band=0;
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

