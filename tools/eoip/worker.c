/* Service entry point for the managed EoIP slots.
 *
 * One command performs one complete action for one slot:
 *   start  SLOT ENABLED AUTOSTART LOCAL REMOTE ID MTU KEEPALIVE RETRIES BRIDGE
 *   stop   SLOT
 *   status SLOT
 *
 * A start with the profile disabled means "this slot must not exist": the slot
 * is stopped through the same verified cleanup path instead of leaving a half
 * created interface. Nothing is created for a slot that was never started, and
 * a name held by a foreign interface is refused rather than adopted.
 *
 * The netlink transport is injected, and main supplies the socket transport,
 * so this file is the same code in the firmware binary and in the test.
 * No tunnel is created here: the caller decides which slots start, and the
 * disabled-by-default boot policy and persistence are separate work. */
#include "controller.h"
#include "table.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WR_EOIP_WORKER_DIRECTORY "/var/run/wr-eoip"
#define WR_EOIP_WORKER_PROFILE_FIELDS 10
#define WR_EOIP_WORKER_MESSAGE 2048

/* 64 and above keep the codes clear of shell conventions. */
enum wr_eoip_worker_result {
    WR_EOIP_WORKER_OK = 0,
    WR_EOIP_WORKER_USAGE = 64,
    WR_EOIP_WORKER_INVALID = 65,
    WR_EOIP_WORKER_REFUSED = 66,
    WR_EOIP_WORKER_UNCONFIRMED = 67,
    WR_EOIP_WORKER_ROLLED_BACK = 68
};

struct wr_eoip_worker {
    struct wr_eoip_transport *transport;
    const char *directory;
};

static void wr_eoip_worker_report(char *message, size_t size, const char *text, int value)
{
    if (!message || !size) return;
    if (value >= 0) snprintf(message, size, "%s %d", text, value);
    else snprintf(message, size, "%s", text);
}

static int wr_eoip_worker_slot(const char *text, unsigned *slot)
{
    return text && slot && wr_eoip_decimal(text, WR_EOIP_SLOTS - 1, slot);
}

static int wr_eoip_worker_stop_slot(struct wr_eoip_worker *worker, unsigned slot,
                                    char *message, size_t size)
{
    struct wr_eoip_ops ops;
    int result;

    wr_eoip_controller_ops(&ops, worker->transport);
    result = wr_eoip_lifecycle_stop(worker->directory, slot, &ops);
    switch (result) {
    case WR_EOIP_OK:
        wr_eoip_worker_report(message, size, "slot stopped", (int)slot);
        return WR_EOIP_WORKER_OK;
    case WR_EOIP_UNCONFIRMED:
        wr_eoip_worker_report(message, size, "cleanup unconfirmed for slot", (int)slot);
        return WR_EOIP_WORKER_UNCONFIRMED;
    default:
        wr_eoip_worker_report(message, size, "cleanup refused for slot", (int)slot);
        return WR_EOIP_WORKER_REFUSED;
    }
}

static int wr_eoip_worker_start(struct wr_eoip_worker *worker, const char *const *fields,
                                char *message, size_t size)
{
    struct wr_eoip_ops ops;
    struct wr_eoip_config config;
    unsigned slot, enabled;
    int result;

    /* Turning a slot off must work even if its old endpoint is corrupt. */
    if (!wr_eoip_worker_slot(fields[0], &slot) ||
        !wr_eoip_decimal(fields[1], 1, &enabled)) {
        wr_eoip_worker_report(message, size, "profile invalid", -1);
        return WR_EOIP_WORKER_INVALID;
    }
    if (!enabled) return wr_eoip_worker_stop_slot(worker, slot, message, size);
    if (!wr_eoip_validate(fields[0], fields[1], fields[2], fields[3], fields[4], fields[5],
                          fields[6], fields[7], fields[8], fields[9], &config)) {
        wr_eoip_worker_report(message, size, "profile invalid", -1);
        return WR_EOIP_WORKER_INVALID;
    }
    wr_eoip_controller_ops(&ops, worker->transport);
    result = wr_eoip_lifecycle_start(worker->directory, &config, &ops);
    switch (result) {
    case WR_EOIP_OK: {
        struct wr_eoip_observation observed;
        unsigned index = 0;
        if (wr_eoip_controller_query(worker->transport, config.slot, &observed) == 2)
            index = (unsigned)observed.ifindex;
        snprintf(message, size, "slot started index %u", index);
        return WR_EOIP_WORKER_OK;
    }
    case WR_EOIP_REFUSED:
        wr_eoip_worker_report(message, size, "start refused for slot", (int)config.slot);
        return WR_EOIP_WORKER_REFUSED;
    case WR_EOIP_ROLLED_BACK:
        wr_eoip_worker_report(message, size, "start rolled back for slot", (int)config.slot);
        return WR_EOIP_WORKER_ROLLED_BACK;
    default:
        wr_eoip_worker_report(message, size, "start unconfirmed for slot", (int)config.slot);
        return WR_EOIP_WORKER_UNCONFIRMED;
    }
}

static int wr_eoip_worker_status(struct wr_eoip_worker *worker, unsigned slot,
                                 char *message, size_t size)
{
    struct wr_eoip_observation observed;
    int present = wr_eoip_controller_query(worker->transport, slot, &observed);

    if (present == 1) {
        wr_eoip_worker_report(message, size, "slot absent", (int)slot);
        return WR_EOIP_WORKER_OK;
    }
    if (present != 2) {
        wr_eoip_worker_report(message, size, "status unknown for slot", (int)slot);
        return WR_EOIP_WORKER_UNCONFIRMED;
    }
    if (!observed.owned) {
        wr_eoip_worker_report(message, size, "slot name held by a foreign interface", (int)slot);
        return WR_EOIP_WORKER_REFUSED;
    }
    snprintf(message, size, "slot owned index %d mtu %u master %u admin-up %u",
             observed.ifindex, observed.mtu, observed.master, observed.flags & 1U);
    return WR_EOIP_WORKER_OK;
}

/* Structured observations for the WebUI. A successful JSON response means the
 * observation was serialized, not that tunnels work or peers are reachable.
 * Strings are fixed literals; no interface names, aliases or endpoints from
 * the kernel/configuration are interpolated into JSON. */
static int wr_eoip_worker_status_json(struct wr_eoip_worker *worker,
                                     char *message, size_t size)
{
    unsigned slot;
    size_t used = 0;
    int n;
    n = snprintf(message, size, "{\"schema\":1,\"slots\":[");
    if (n < 0 || (size_t)n >= size) return WR_EOIP_WORKER_UNCONFIRMED;
    used = (size_t)n;
    for (slot = 0; slot < WR_EOIP_SLOTS; slot++) {
        struct wr_eoip_observation observed;
        int present = wr_eoip_controller_query(worker->transport, slot, &observed);
        const char *state = present == 1 ? "absent" :
            present != 2 ? "unknown" : !observed.owned ? "foreign" :
            (observed.flags & 1U) ? "up" : "down";
        if (present == 2 && observed.owned)
            n = snprintf(message + used, size - used,
                "%s{\"slot\":%u,\"state\":\"%s\",\"ifindex\":%d,\"mtu\":%u,\"master\":%u}",
                slot ? "," : "", slot, state, observed.ifindex, observed.mtu, observed.master);
        else
            n = snprintf(message + used, size - used,
                "%s{\"slot\":%u,\"state\":\"%s\"}", slot ? "," : "", slot, state);
        if (n < 0 || (size_t)n >= size - used) goto truncated;
        used += (size_t)n;
    }
    n = snprintf(message + used, size - used, "]}");
    if (n < 0 || (size_t)n >= size - used) goto truncated;
    return WR_EOIP_WORKER_OK;
truncated:
    wr_eoip_worker_report(message, size, "status output buffer too small", -1);
    return WR_EOIP_WORKER_UNCONFIRMED;
}

/* Returns one of the wr_eoip_worker_result codes and never exits the process. */
static int wr_eoip_worker_dispatch_unlocked(struct wr_eoip_worker *worker, int argc, char **argv,
                                   char *message, size_t size)
{
    const char *fields[WR_EOIP_WORKER_PROFILE_FIELDS];
    unsigned slot;
    int i;

    if (message && size) message[0] = '\0';
    if (!worker || !worker->transport || !worker->directory || !message || size < 1) {
        wr_eoip_worker_report(message, size, "worker not configured", -1);
        return WR_EOIP_WORKER_USAGE;
    }
    if (argc < 2 || !argv || !argv[1]) {
        wr_eoip_worker_report(message, size, "usage: start|stop|status", -1);
        return WR_EOIP_WORKER_USAGE;
    }
    if (!strcmp(argv[1], "status-json")) {
        if (argc != 2) return WR_EOIP_WORKER_USAGE;
        return wr_eoip_worker_status_json(worker, message, size);
    }
    if (!strcmp(argv[1], "boot-table")) {
        struct wr_eoip_config profiles[WR_EOIP_SLOTS];
        unsigned n, enabled, autostart;
        int combined = WR_EOIP_WORKER_OK;
        /* Exactly eight snapshots, ten fields per slot, before any mutation. */
        if (argc != 2 + WR_EOIP_SLOTS * WR_EOIP_WORKER_PROFILE_FIELDS) {
            wr_eoip_worker_report(message, size, "boot table needs eight profiles", -1);
            return WR_EOIP_WORKER_USAGE;
        }
        memset(profiles, 0, sizeof(profiles));
        for (n = 0; n < WR_EOIP_SLOTS; n++) {
            const char *const *f = (const char *const *)&argv[2 + n * 10];
            if (!wr_eoip_worker_slot(f[0], &slot) || slot != n ||
                !wr_eoip_decimal(f[1], 1, &enabled) ||
                !wr_eoip_decimal(f[2], 1, &autostart)) {
                wr_eoip_worker_report(message, size, "boot table flags invalid", (int)n);
                return WR_EOIP_WORKER_INVALID;
            }
            profiles[n].slot = slot;
            if (!enabled) continue; /* Empty disabled endpoints are valid. */
            if (!wr_eoip_validate(f[0], f[1], f[2], f[3], f[4], f[5],
                                  f[6], f[7], f[8], f[9], &profiles[n])) {
                wr_eoip_worker_report(message, size, "boot table profile invalid", (int)n);
                return WR_EOIP_WORKER_INVALID;
            }
        }
        if (!wr_eoip_table_valid(profiles, WR_EOIP_SLOTS)) {
            wr_eoip_worker_report(message, size, "profile table conflicts", -1);
            return WR_EOIP_WORKER_INVALID;
        }
        for (n = 0; n < WR_EOIP_SLOTS; n++) {
            int code;
            if (!profiles[n].enabled || !profiles[n].autostart) continue;
            code = wr_eoip_worker_start(worker,
                (const char *const *)&argv[2 + n * 10], message, size);
            if (code != WR_EOIP_WORKER_OK) combined = code;
        }
        wr_eoip_worker_report(message, size,
            combined ? "boot table incomplete" : "boot table applied", -1);
        return combined;
    }
    if (!strcmp(argv[1], "start")) {
        if (argc != 2 + WR_EOIP_WORKER_PROFILE_FIELDS) {
            wr_eoip_worker_report(message, size, "usage: start needs 10 profile fields", -1);
            return WR_EOIP_WORKER_USAGE;
        }
        for (i = 0; i < WR_EOIP_WORKER_PROFILE_FIELDS; i++) fields[i] = argv[2 + i];
        return wr_eoip_worker_start(worker, fields, message, size);
    }
    if (!strcmp(argv[1], "stop") || !strcmp(argv[1], "status")) {
        if (argc != 3 || !wr_eoip_worker_slot(argv[2], &slot)) {
            wr_eoip_worker_report(message, size, "usage: stop|status SLOT", -1);
            return WR_EOIP_WORKER_USAGE;
        }
        if (!strcmp(argv[1], "stop")) return wr_eoip_worker_stop_slot(worker, slot, message, size);
        return wr_eoip_worker_status(worker, slot, message, size);
    }
    wr_eoip_worker_report(message, size, "usage: start|stop|status", -1);
    return WR_EOIP_WORKER_USAGE;
}

/* All managed mutations share one operation lock, including the complete table.
 * The per-slot lifecycle still acquires the distinct registry lock internally.
 * Status remains read-only and never waits for a mutation to finish. */
static int wr_eoip_worker_dispatch(struct wr_eoip_worker *worker, int argc, char **argv,
                                   char *message, size_t size)
{
    struct wr_eoip_state operation = {.fd = -1};
    int result;
    if (!worker || !worker->directory || !argv || argc < 2 || !argv[1] ||
        (!strcmp(argv[1], "status")) ||
        (strcmp(argv[1], "start") && strcmp(argv[1], "stop") && strcmp(argv[1], "boot-table")))
        return wr_eoip_worker_dispatch_unlocked(worker, argc, argv, message, size);
    if (!wr_eoip_state_lock_named(worker->directory, &operation, "operation-lock")) {
        wr_eoip_worker_report(message, size, "operation busy or state directory unavailable", -1);
        return WR_EOIP_WORKER_REFUSED;
    }
    result = wr_eoip_worker_dispatch_unlocked(worker, argc, argv, message, size);
    wr_eoip_state_unlock(&operation);
    return result;
}

#ifndef WR_EOIP_WORKER_NO_MAIN
static int wr_eoip_socket_query(void *context, const char *name, const char *owner,
                                struct wr_eoip_observation *out)
{
    (void)context;
    return wr_eoip_query_link(name, owner, out);
}

int main(int argc, char **argv)
{
    struct wr_eoip_transport transport;
    struct wr_eoip_worker worker;
    const char *directory = getenv("WR_EOIP_STATE_DIR");
    char message[WR_EOIP_WORKER_MESSAGE];
    int result;

    transport.context = NULL;
    transport.talk = wr_eoip_socket_talk;
    transport.query = wr_eoip_socket_query;
    worker.transport = &transport;
    worker.directory = (directory && *directory) ? directory : WR_EOIP_WORKER_DIRECTORY;
    result = wr_eoip_worker_dispatch(&worker, argc, argv, message, sizeof(message));
    if (result == WR_EOIP_WORKER_OK) {
        fprintf(stdout, "%s\n", message);
    } else {
        fprintf(stderr, "%s\n", message);
    }
    return result;
}
#endif
