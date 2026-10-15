#include <assert.h>
#include "settings.h"
struct fixture {
    const struct wr_eoip_settings *plan;
    char values[73][48]; int exists[73];
    unsigned reads, writes, fail_write; int fail_read, fail_rollback;
};
static unsigned lookup(struct fixture *f, const char *key)
{
    unsigned i;
    for (i = 0; i < f->plan->count; i++) if (!strcmp(key, f->plan->entries[i].key)) return i;
    assert(0); return 0;
}
static int read_value(void *context, const char *key, char *out, size_t size, int *exists)
{
    struct fixture *f = context; unsigned i = lookup(f, key);
    f->reads++;
    if (f->fail_read) return 0;
    assert(strlen(f->values[i]) < size);
    strcpy(out, f->values[i]); *exists = f->exists[i]; return 1;
}
static int write_value(void *context, const char *key, const char *value)
{
    struct fixture *f = context; unsigned i = lookup(f, key);
    f->writes++; f->exists[i] = value != NULL;
    strcpy(f->values[i], value ? value : "");
    if (f->writes == f->fail_write ||
        (f->fail_rollback && f->writes == f->fail_write + 1)) return 0;
    return 1;
}
int main(void)
{
    struct wr_eoip_settings plan;
    struct fixture f;
    struct wr_eoip_settings_io io = {&f, read_value, write_value};
    const char *fields[8][9]; unsigned slot, key;
    assert(wr_eoip_settings_prepare("0", NULL, &plan) && plan.count == 1);
    assert(!strcmp(plan.entries[0].key, "eoip_enable"));
    assert(!wr_eoip_settings_prepare("bad", NULL, &plan) && !plan.count);
    for (slot = 0; slot < 8; slot++) {
        for (key = 0; key < 9; key++) fields[slot][key] = "";
        fields[slot][0] = fields[slot][1] = "0";
    }
    assert(wr_eoip_settings_prepare("1", fields, &plan) && plan.count == 73);
    memset(&f, 0, sizeof(f)); f.plan = &plan;
    assert(wr_eoip_settings_write(&plan, &io) == WR_EOIP_SETTINGS_OK);
    assert(f.reads == 73 && f.writes == 73 && !strcmp(f.values[0], "1"));
    memset(&f, 0, sizeof(f)); f.plan = &plan; f.fail_read = 1;
    assert(wr_eoip_settings_write(&plan, &io) == WR_EOIP_SETTINGS_REFUSED && !f.writes);
    memset(&f, 0, sizeof(f)); f.plan = &plan; f.fail_write = 7;
    f.exists[2] = 1; strcpy(f.values[2], "old");
    assert(wr_eoip_settings_write(&plan, &io) == WR_EOIP_SETTINGS_ROLLED_BACK);
    assert(f.exists[2] && !strcmp(f.values[2], "old") && !f.exists[1] && !f.exists[0]);
    memset(&f, 0, sizeof(f)); f.plan = &plan; f.fail_write = 7; f.fail_rollback = 1;
    assert(wr_eoip_settings_write(&plan, &io) == WR_EOIP_SETTINGS_UNCONFIRMED);
    for (slot = 0; slot < 2; slot++) {
        const char *valid[9] = {"1", "1", "10.0.0.1", "10.0.0.2", "7", "1458", "0", "0", ""};
        for (key = 0; key < 9; key++) fields[slot][key] = valid[key];
    }
    assert(!wr_eoip_settings_prepare("1", fields, &plan) && !plan.count);
    fields[1][4] = "8";
    assert(wr_eoip_settings_prepare("1", fields, &plan));
    fields[0][8] = "br0\nunsafe";
    assert(!wr_eoip_settings_prepare("1", fields, &plan));
    assert(wr_eoip_settings_prepare("0", fields, &plan) && plan.count == 1);
    puts("PASS EoIP settings: validation, disable, fixed keys, snapshot-before-write and rollback outcomes");
    return 0;
}
