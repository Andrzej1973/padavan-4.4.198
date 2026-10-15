#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "runtime-state.h"
#define BOARD_WR1200JS 1
#define APP_EOIP 1
#define RCN_APPLY_EOIP "apply_eoip"
static char directory[] = "/tmp/wr-eoip-http-XXXXXX";
#define WR_EOIP_SETTINGS_DIRECTORY directory
typedef FILE *webs_t;
static int safe = 1, method_post = 1, writes, notified, invalidated;
static const char *submitted_token = "0123456789abcdef0123456789abcdef", *ack = "1", *master = "0";
static int websWrite(FILE *out, const char *format, ...)
{ int n; va_list args; va_start(args, format); n = vfprintf(out, format, args); va_end(args); return n; }
static int get_login_safe(void) { return safe; }
int wr_eoip_request_is_post(void) { return method_post; }
static unsigned parsed_bodies;
static void init_cgi(char *body) { if (body) parsed_bodies++; }
static const char *websGetVar(FILE *stream, const char *key, const char *fallback)
{
    (void)stream;
    if (!strcmp(key, "token")) return submitted_token;
    if (!strcmp(key, "ack")) return ack;
    if (!strcmp(key, "eoip_enable")) return master;
    return fallback;
}
static char *nvram_get(const char *key)
{
    struct wr_eoip_state contender = {.fd = -1};
    assert(!wr_eoip_state_lock_named(directory, &contender, "operation-lock"));
    return !strcmp(key, "eoip_enable") ? "1" : "\"quoted\\value";
}
static int nvram_set(const char *key, const char *value)
{ assert(!strcmp(key, "eoip_enable") && !strcmp(value, "0")); writes++; return 0; }
static int nvram_unset(const char *key) { (void)key; assert(0); return -1; }
static void notify_rc(const char *event)
{
    struct wr_eoip_state held = {.fd = -1};
    assert(!strcmp(event, "apply_eoip"));
    assert(wr_eoip_state_lock_named(directory, &held, "operation-lock"));
    wr_eoip_state_unlock(&held); notified++;
}
void wr_eoip_status_invalidate(void) { invalidated++; }
#include "http-settings.inc"
int main(int argc, char **argv)
{
    FILE *out = tmpfile(), *input;
    char path[PATH_MAX], body[] = "%00", reply[256];
    char *settings_json;
    long settings_length;
    struct wr_eoip_state held = {.fd = -1};
    assert(out && mkdtemp(directory));
    strcpy(wr_eoip_csrf, "0123456789abcdef0123456789abcdef");
    assert(ej_wr_eoip_token(0, out, 0, NULL) > 0);
    assert(ej_wr_eoip_settings(0, out, 0, NULL) > 0);
    {
        FILE *json = tmpfile(); assert(json);
        assert(ej_wr_eoip_settings(0, json, 0, NULL) > 0);
        assert(!fflush(json)); settings_length = ftell(json); assert(settings_length > 0);
        settings_json = calloc((size_t)settings_length + 1, 1); assert(settings_json);
        rewind(json);
        assert(fread(settings_json, 1, (size_t)settings_length, json) == (size_t)settings_length);
        fclose(json);
        assert(strstr(settings_json, "\\\"quoted\\\\value"));
    }
    wr_eoip_settings_output("", out); assert(!writes && !notified);
    wr_eoip_post_valid = 1; safe = 0;
    wr_eoip_settings_output("", out); assert(!writes); safe = 1;
    wr_eoip_post_valid = 1; method_post = 0;
    wr_eoip_settings_output("", out); assert(!writes); method_post = 1;
    wr_eoip_post_valid = 1; submitted_token = "bad";
    wr_eoip_settings_output("", out); assert(!writes);
    submitted_token = wr_eoip_csrf;
    wr_eoip_post_valid = 1; ack = "0";
    wr_eoip_settings_output("", out); assert(!writes); ack = "1";
    assert(wr_eoip_state_lock_named(directory, &held, "operation-lock"));
    wr_eoip_post_valid = 1;
    wr_eoip_settings_output("", out); assert(!writes);
    wr_eoip_state_unlock(&held);
    input = fmemopen(body, strlen(body), "r"); assert(input);
    wr_eoip_settings_input("", input, (int)strlen(body), NULL); fclose(input);
    assert(!wr_eoip_post_valid);
    {
        const char *invalid[] = {"%", "%0", "%GG", "token=x%0Z"};
        unsigned i;
        for (i = 0; i < sizeof(invalid)/sizeof(invalid[0]); i++) {
            input = fmemopen((void *)invalid[i], strlen(invalid[i]), "r"); assert(input);
            wr_eoip_settings_input("", input, (int)strlen(invalid[i]), NULL); fclose(input);
            assert(!wr_eoip_post_valid && !parsed_bodies);
        }
        input = fmemopen(body, strlen(body), "r"); assert(input);
        wr_eoip_settings_input("", input, (int)strlen(body)+2, NULL); fclose(input);
        assert(!wr_eoip_post_valid && !parsed_bodies);
        {
            char valid[] = "token=%41&ack=1", embedded[] = {'a',0,'b'};
            input = fmemopen(embedded, sizeof(embedded), "r"); assert(input);
            wr_eoip_settings_input("", input, sizeof(embedded), NULL); fclose(input);
            assert(!wr_eoip_post_valid && !parsed_bodies);
            input = fmemopen(valid, strlen(valid), "r"); assert(input);
            wr_eoip_settings_input("", input, (int)strlen(valid), NULL); fclose(input);
            assert(wr_eoip_post_valid && parsed_bodies == 1);
        }
    }
    fclose(out); out = tmpfile(); assert(out);
    wr_eoip_post_valid = 1;
    wr_eoip_settings_output("", out);
    assert(writes == 1 && notified == 1 && invalidated == 1 && !wr_eoip_post_valid);
    rewind(out); memset(reply, 0, sizeof(reply)); assert(fread(reply, 1, sizeof(reply)-1, out) > 0);
    assert(strstr(reply, "\"saved_in_ram\":true") && strstr(reply, "\"applied\":null"));
    wr_eoip_settings_output("", out); assert(writes == 1);
    fclose(out);
    snprintf(path, sizeof(path), "%s/operation-lock", directory); unlink(path);
    assert(!rmdir(directory));
    if (argc == 2 && !strcmp(argv[1], "--json")) puts(settings_json);
    else puts("PASS EoIP HTTP settings: guards, request encoding, snapshot escaping and RAM-only write");
    free(settings_json);
    return 0;
}
