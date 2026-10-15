#include <assert.h>
#define WR_EOIP_WORKER_NO_MAIN
#include "worker.c"
#include "stored.h"
struct fixture { const char *directory, *master; unsigned reads; char scratch[48]; };
static const char *read_value(void *context, const char *key)
{
    struct fixture *f = context;
    if (++f->reads > 1) {
        struct wr_eoip_state contender = {.fd = -1};
        assert(!wr_eoip_state_lock_named(f->directory, &contender, "operation-lock"));
    }
    if (!strcmp(key, "eoip_enable")) snprintf(f->scratch, sizeof(f->scratch), "%s", f->master);
    else if (strstr(key, "_enable") || strstr(key, "_autostart")) strcpy(f->scratch, "0");
    else snprintf(f->scratch, sizeof(f->scratch), "unused value for %s", key);
    return f->scratch; /* Deliberately invalidated on the next read. */
}
static int query(void *context, const char *name, const char *owner, struct wr_eoip_observation *out)
{ (void)context; (void)name; (void)owner; memset(out, 0, sizeof(*out)); return 1; }
static int talk(void *context, const void *data, size_t size, uint32_t sequence)
{ (void)context; (void)data; (void)size; (void)sequence; assert(0); return 1; }
int main(void)
{
    char directory[] = "/tmp/wr-eoip-stored-XXXXXX", path[PATH_MAX], message[2048];
    struct wr_eoip_transport transport = {NULL, talk, query};
    struct wr_eoip_worker worker = {&transport, directory};
    struct fixture f = {directory, "0", 0, ""};
    struct stat st;
    char *status[] = {"eoip-service", "status", "0"};
    assert(mkdtemp(directory)); assert(!rmdir(directory));
    assert(wr_eoip_stored_dispatch(&worker, "boot-stored", read_value, &f, NULL, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(lstat(directory, &st) != 0 && errno == ENOENT && f.reads == 1);
    f.master = "1"; f.reads = 0;
    assert(wr_eoip_stored_dispatch(&worker, "boot-stored", read_value, &f, NULL, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(f.reads == 74 && strstr(message, "table applied"));
    f.master = "0"; f.reads = 0;
    assert(wr_eoip_stored_dispatch(&worker, "apply-stored", read_value, &f, NULL, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(f.reads == 2 && strstr(message, "table stopped"));
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    {
        struct wr_eoip_state held = {.fd = -1};
        assert(wr_eoip_state_lock_named(directory, &held, "operation-lock"));
        f.master = "1"; f.reads = 0;
        assert(wr_eoip_stored_dispatch(&worker, "apply-stored", read_value, &f, NULL, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
        assert(f.reads == 1);
        wr_eoip_state_unlock(&held);
    }
    snprintf(path, sizeof(path), "%s/operation-lock", directory); unlink(path);
    snprintf(path, sizeof(path), "%s/lock", directory); unlink(path);
    assert(!rmdir(directory));
    puts("PASS EoIP stored snapshot: lock during every profile read, disabled no-op, cleanup and contention");
    return 0;
}
