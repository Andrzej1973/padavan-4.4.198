#ifndef WR_BAND_PROFILE_POLICY_H
#define WR_BAND_PROFILE_POLICY_H
struct wr_band_credentials {
    int radio_enabled, hidden, wep_enabled, wpa_mode;
    const char *ssid, *auth_mode, *crypto, *psk;
};
enum wr_band_profile_result {
    WR_PROFILE_DISABLED = 0, WR_PROFILE_COMPATIBLE = 1,
    WR_PROFILE_INVALID = -1, WR_PROFILE_RADIO_OFF = -2,
    WR_PROFILE_MISMATCH = -3, WR_PROFILE_UNSUPPORTED_SECURITY = -4,
    WR_PROFILE_AP_UNAVAILABLE = -5
};
/* Read-only: validates borrowed configuration strings; never modifies NVRAM. */
int wr_band_profile_validate(int requested, const struct wr_band_credentials bands[2]);
typedef const char *(*wr_band_setting_getter)(int band, const char *name, void *context);
/* The caller must serialize settings updates across this snapshot and activation. */
int wr_band_profile_from_settings(int requested, wr_band_setting_getter get, void *context);
#endif

