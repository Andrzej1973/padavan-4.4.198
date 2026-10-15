#if defined(BOARD_WR1200JS) && defined(APP_EOIP)
#include "wr-eoip/settings.h"
#include "wr-eoip/runtime-state.h"
#include <ctype.h>
#ifndef WR_EOIP_SETTINGS_DIRECTORY
#define WR_EOIP_SETTINGS_DIRECTORY "/var/run/wr-eoip"
#endif
static char wr_eoip_csrf[33], wr_eoip_post_body[12289];
static int wr_eoip_post_valid;
extern int wr_eoip_request_is_post(void);
extern void wr_eoip_status_invalidate(void);

static int ej_wr_eoip_token(int eid, webs_t wp, int argc, char **argv)
{
    unsigned char random[16];
    int fd, i;
    ssize_t got;
    (void)eid; (void)argv;
    if (argc || !get_login_safe()) return websWrite(wp, "\"\"");
    if (!wr_eoip_csrf[0]) {
        fd = open("/dev/urandom", O_RDONLY);
        if (fd < 0) return websWrite(wp, "\"\"");
        got = read(fd, random, sizeof(random)); close(fd);
        if (got != (ssize_t)sizeof(random)) return websWrite(wp, "\"\"");
        for (i = 0; i < 16; i++) snprintf(wr_eoip_csrf + i * 2, 3, "%02x", random[i]);
    }
    return websWrite(wp, "\"%s\"", wr_eoip_csrf);
}
static void wr_eoip_settings_input(const char *url, FILE *stream, int clen, char *boundary)
{
    size_t used = 0;
    (void)url; (void)boundary;
    wr_eoip_post_valid = 0; init_cgi(NULL);
    if (clen <= 0 || clen >= (int)sizeof(wr_eoip_post_body)) {
        while (clen-- > 0) if (fgetc(stream) == EOF) break;
        return;
    }
    while (used < (size_t)clen) {
        size_t n = fread(wr_eoip_post_body + used, 1, (size_t)clen - used, stream);
        if (!n) return;
        used += n;
    }
    wr_eoip_post_body[used] = 0;
    if (strlen(wr_eoip_post_body) != used) return;
    /* The base decoder assumes every percent escape contains two hex digits.
     * Check that precondition and reject encoded NUL before invoking it. */
    {
        size_t i;
        for (i = 0; i < used; i++) if (wr_eoip_post_body[i] == '%') {
            if (i + 2 >= used || !isxdigit((unsigned char)wr_eoip_post_body[i+1]) ||
                !isxdigit((unsigned char)wr_eoip_post_body[i+2]) ||
                (wr_eoip_post_body[i+1] == '0' && wr_eoip_post_body[i+2] == '0')) return;
            i += 2;
        }
    }
    init_cgi(wr_eoip_post_body);
    wr_eoip_post_valid = 1;
}
static int wr_eoip_settings_read_nvram(void *context, const char *key, char *out, size_t size, int *exists)
{
    const char *value = nvram_get(key);
    size_t length;
    (void)context;
    *exists = value != NULL;
    if (!value) { out[0] = 0; return 1; }
    length = strlen(value);
    if (length >= size) return 0;
    memcpy(out, value, length + 1); return 1;
}
static int wr_eoip_settings_write_nvram(void *context, const char *key, const char *value)
{
    (void)context;
    return (value ? nvram_set(key, value) : nvram_unset(key)) == 0;
}
static int wr_eoip_json_string(webs_t stream, const char *value)
{
    int written = websWrite(stream, "\"");
    const unsigned char *p = (const unsigned char *)value;
    for (; *p; p++) {
        if (*p == '"' || *p == '\\') written += websWrite(stream, "\\%c", *p);
        else if (*p < 32) written += websWrite(stream, "\\u%04x", (unsigned)*p);
        else written += websWrite(stream, "%c", *p);
    }
    return written + websWrite(stream, "\"");
}
static int ej_wr_eoip_settings(int eid, webs_t wp, int argc, char **argv)
{
    static const char *keys[9] = {"enable", "autostart", "local", "remote", "id", "mtu", "keepalive", "retries", "bridge"};
    char values[73][48], key[32];
    struct wr_eoip_state lock = {.fd = -1};
    unsigned slot, field;
    int exists, valid = 1, written;
    (void)eid; (void)argv;
    if (argc || !get_login_safe()) return websWrite(wp, "{\"error\":\"unsafe_request\"}");
    if (!wr_eoip_state_lock_named(WR_EOIP_SETTINGS_DIRECTORY, &lock, "operation-lock"))
        return websWrite(wp, "{\"error\":\"busy_or_unavailable\"}");
    if (!wr_eoip_settings_read_nvram(NULL, "eoip_enable", values[0], sizeof(values[0]), &exists)) valid = 0;
    else if (!exists) strcpy(values[0], "0");
    for (slot = 0; slot < 8; slot++) for (field = 0; field < 9; field++) {
        snprintf(key, sizeof(key), "eoip_slot%u_%s", slot, keys[field]);
        if (!wr_eoip_settings_read_nvram(NULL, key, values[1 + slot*9 + field], 48, &exists)) valid = 0;
    }
    wr_eoip_state_unlock(&lock);
    if (!valid) return websWrite(wp, "{\"error\":\"stored_settings_unavailable\"}");
    written = websWrite(wp, "{\"schema\":1,\"master\":");
    written += wr_eoip_json_string(wp, values[0]);
    written += websWrite(wp, ",\"slots\":[");
    for (slot = 0; slot < 8; slot++) {
        written += websWrite(wp, "%s{\"slot\":%u", slot ? "," : "", slot);
        for (field = 0; field < 9; field++) {
            written += websWrite(wp, ",\"%s\":", keys[field]);
            written += wr_eoip_json_string(wp, values[1 + slot*9 + field]);
        }
        written += websWrite(wp, "}");
    }
    return written + websWrite(wp, "]}");
}
static void wr_eoip_settings_output(const char *url, FILE *stream)
{
    static const char *keys[9] = {"enable", "autostart", "local", "remote", "id", "mtu", "keepalive", "retries", "bridge"};
    struct wr_eoip_settings plan;
    struct wr_eoip_state lock = {.fd = -1};
    struct wr_eoip_settings_io io = {NULL, wr_eoip_settings_read_nvram, wr_eoip_settings_write_nvram};
    const char *fields[8][9], *token;
    char key[32];
    unsigned slot, field;
    int posted = wr_eoip_post_valid, result;
    (void)url; wr_eoip_post_valid = 0;
    if (!posted || !wr_eoip_request_is_post() || !get_login_safe()) {
        websWrite(stream, "{\"error\":\"unsafe_request\"}"); return;
    }
    token = websGetVar(stream, "token", "");
    if (!wr_eoip_csrf[0] || strlen(token) != 32 || strcmp(token, wr_eoip_csrf) ||
        strcmp(websGetVar(stream, "ack", ""), "1")) {
        websWrite(stream, "{\"error\":\"invalid_token_or_confirmation\"}"); return;
    }
    for (slot = 0; slot < 8; slot++) for (field = 0; field < 9; field++) {
        snprintf(key, sizeof(key), "eoip_slot%u_%s", slot, keys[field]);
        fields[slot][field] = websGetVar(stream, key, "");
    }
    if (!wr_eoip_settings_prepare(websGetVar(stream, "eoip_enable", ""), fields, &plan)) {
        websWrite(stream, "{\"error\":\"invalid_settings\"}"); return;
    }
    if (!wr_eoip_state_lock_named(WR_EOIP_SETTINGS_DIRECTORY, &lock, "operation-lock")) {
        websWrite(stream, "{\"error\":\"busy_or_unavailable\"}"); return;
    }
    result = wr_eoip_settings_write(&plan, &io);
    wr_eoip_state_unlock(&lock);
    if (result != WR_EOIP_SETTINGS_OK) {
        const char *error = result == WR_EOIP_SETTINGS_ROLLED_BACK ? "settings_rolled_back" :
            result == WR_EOIP_SETTINGS_UNCONFIRMED ? "settings_unconfirmed" : "settings_refused";
        websWrite(stream, "{\"error\":\"%s\"}", error); return;
    }
    wr_eoip_status_invalidate();
    /* Notify only after releasing operation-lock, or rc could lose the Apply
     * by observing lock contention. notify_rc returns void: do not claim an
     * acknowledged queue entry or successful tunnel application. */
    notify_rc(RCN_APPLY_EOIP);
    websWrite(stream, "{\"saved_in_ram\":true,\"apply_requested\":true,\"applied\":null}");
}
#endif
