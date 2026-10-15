#ifndef WR_EOIP_SETTINGS_H
#define WR_EOIP_SETTINGS_H
#include "table.h"
#include <stdio.h>
#define WR_EOIP_SETTING_COUNT 73
#define WR_EOIP_SETTING_SIZE 48
struct wr_eoip_setting { char key[32], value[WR_EOIP_SETTING_SIZE]; };
struct wr_eoip_settings { unsigned count; struct wr_eoip_setting entries[WR_EOIP_SETTING_COUNT]; };
/* Caller supplies one complete form snapshot, fields in schema order.
 * Master-off intentionally ignores endpoint fields so disabling always works. */
static inline int wr_eoip_settings_prepare(const char *master,
    const char *fields[8][9], struct wr_eoip_settings *out)
{
    static const char *keys[9] = {"enable", "autostart", "local", "remote", "id", "mtu", "keepalive", "retries", "bridge"};
    struct wr_eoip_config profiles[8];
    unsigned enabled, slot, field;
    if (!out) return 0;
    memset(out, 0, sizeof(*out)); memset(profiles, 0, sizeof(profiles));
    if (!wr_eoip_decimal(master, 1, &enabled)) return 0;
    strcpy(out->entries[0].key, "eoip_enable");
    strcpy(out->entries[0].value, enabled ? "1" : "0");
    out->count = 1;
    if (!enabled) return 1;
    if (!fields) goto invalid;
    for (slot = 0; slot < 8; slot++) {
        char number[2] = {(char)('0' + slot), 0};
        unsigned slot_enabled, automatic;
        profiles[slot].slot = slot;
        for (field = 0; field < 9; field++) {
            const char *value = fields[slot][field];
            size_t n, length;
            struct wr_eoip_setting *entry = &out->entries[out->count];
            if (!value || (length = strlen(value)) >= WR_EOIP_SETTING_SIZE) goto invalid;
            for (n = 0; n < length; n++)
                if ((unsigned char)value[n] < 32 || (unsigned char)value[n] == 127) goto invalid;
            snprintf(entry->key, sizeof(entry->key), "eoip_slot%u_%s", slot, keys[field]);
            memcpy(entry->value, value, length + 1); out->count++;
        }
        if (!wr_eoip_decimal(fields[slot][0], 1, &slot_enabled) ||
            !wr_eoip_decimal(fields[slot][1], 1, &automatic)) goto invalid;
        if (slot_enabled && !wr_eoip_validate(number, fields[slot][0], fields[slot][1],
            fields[slot][2], fields[slot][3], fields[slot][4], fields[slot][5],
            fields[slot][6], fields[slot][7], fields[slot][8], &profiles[slot])) goto invalid;
    }
    if (!wr_eoip_table_valid(profiles, 8)) goto invalid;
    return 1;
invalid:
    memset(out, 0, sizeof(*out)); return 0;
}
struct wr_eoip_settings_io {
    void *context;
    /* read copies a bounded old value and presence; callbacks return 1 on success.
     * write(NULL) restores an absent key. No callback may commit flash here. */
    int (*read)(void *, const char *, char *, size_t, int *);
    int (*write)(void *, const char *, const char *);
};
enum wr_eoip_settings_result { WR_EOIP_SETTINGS_OK, WR_EOIP_SETTINGS_REFUSED,
    WR_EOIP_SETTINGS_ROLLED_BACK, WR_EOIP_SETTINGS_UNCONFIRMED };
/* Caller holds the configuration transaction lock. This is best-effort RAM
 * NVRAM rollback, not atomic persistence across process failure or power loss.
 * Invoke rc only after OK, never after a partial or unconfirmed write. */
static inline int wr_eoip_settings_write(const struct wr_eoip_settings *plan,
                                         const struct wr_eoip_settings_io *io)
{
    char old[WR_EOIP_SETTING_COUNT][WR_EOIP_SETTING_SIZE];
    int exists[WR_EOIP_SETTING_COUNT];
    unsigned i;
    if (!plan || !io || !io->read || !io->write ||
        (plan->count != 1 && plan->count != WR_EOIP_SETTING_COUNT)) return WR_EOIP_SETTINGS_REFUSED;
    memset(old, 0, sizeof(old)); memset(exists, 0, sizeof(exists));
    for (i = 0; i < plan->count; i++) {
        if (!io->read(io->context, plan->entries[i].key, old[i], sizeof(old[i]), &exists[i]) ||
            (exists[i] != 0 && exists[i] != 1) || !memchr(old[i], 0, sizeof(old[i])))
            return WR_EOIP_SETTINGS_REFUSED;
    }
    for (i = 0; i < plan->count; i++) {
        unsigned current = (i + 1) % plan->count; /* Publish master last. */
        if (!io->write(io->context, plan->entries[current].key, plan->entries[current].value)) {
            int restored = 1;
            /* A failed callback may have changed its key: restore it as well. */
            unsigned remaining = i + 1;
            while (remaining) {
                unsigned index = ((--remaining) + 1) % plan->count;
                if (!io->write(io->context, plan->entries[index].key,
                    exists[index] ? old[index] : NULL)) restored = 0;
            }
            return restored ? WR_EOIP_SETTINGS_ROLLED_BACK : WR_EOIP_SETTINGS_UNCONFIRMED;
        }
    }
    return WR_EOIP_SETTINGS_OK;
}
#endif
