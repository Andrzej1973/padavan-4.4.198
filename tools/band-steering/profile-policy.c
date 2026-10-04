#include "profile-policy.h"
#include <stddef.h>
#include <string.h>
static int bounded_text(const char *s, size_t maximum, size_t *length)
{
    size_t n;
    if (!s) return 0;
    for (n = 0; n <= maximum; ++n) {
        if (!s[n]) { *length = n; return 1; }
        if (s[n] == '\r' || s[n] == '\n') return 0;
    }
    return 0;
}
static int valid_psk(const char *s)
{
    size_t n, i;
    if (!bounded_text(s, 64, &n) || n < 8) return 0;
    for (i = 0; i < n; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (n == 64) {
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return 0;
        } else if (c < 32 || c > 126) return 0;
    }
    return 1;
}
static int security(const struct wr_band_credentials *b)
{
    size_t length;
    if (!bounded_text(b->auth_mode, 16, &length)) return WR_PROFILE_INVALID;
    if (b->wep_enabled) return WR_PROFILE_UNSUPPORTED_SECURITY;
    if (!strcmp(b->auth_mode, "open")) return 0;
    if (strcmp(b->auth_mode, "psk")) return WR_PROFILE_UNSUPPORTED_SECURITY;
    if (b->wpa_mode != 0 && b->wpa_mode != 1 && b->wpa_mode != 2) return WR_PROFILE_INVALID;
    if (!bounded_text(b->crypto, 16, &length) || !valid_psk(b->psk)) return WR_PROFILE_INVALID;
    if (strcmp(b->crypto, "aes") && strcmp(b->crypto, "tkip") && strcmp(b->crypto, "tkip+aes"))
        return WR_PROFILE_UNSUPPORTED_SECURITY;
    return 1;
}
int wr_band_profile_validate(int requested, const struct wr_band_credentials bands[2])
{
    size_t i, length; int modes[2];
    if (!requested) return WR_PROFILE_DISABLED;
    if (requested != 1 || !bands) return WR_PROFILE_INVALID;
    for (i = 0; i < 2; ++i) {
        const struct wr_band_credentials *b = &bands[i];
        if (b->radio_enabled != 1) return WR_PROFILE_RADIO_OFF;
        if ((b->hidden != 0 && b->hidden != 1) || (b->wep_enabled != 0 && b->wep_enabled != 1) ||
            !bounded_text(b->ssid, 32, &length) || !length) return WR_PROFILE_INVALID;
        modes[i] = security(b);
        if (modes[i] < 0) return modes[i];
    }
    if (strcmp(bands[0].ssid, bands[1].ssid) || bands[0].hidden != bands[1].hidden || modes[0] != modes[1])
        return WR_PROFILE_MISMATCH;
    if (modes[0] && (bands[0].wpa_mode != bands[1].wpa_mode ||
        strcmp(bands[0].crypto, bands[1].crypto) || strcmp(bands[0].psk, bands[1].psk))) return WR_PROFILE_MISMATCH;
    return WR_PROFILE_COMPATIBLE;
}

