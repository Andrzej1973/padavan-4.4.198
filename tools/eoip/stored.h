#ifndef WR_EOIP_STORED_H
#define WR_EOIP_STORED_H
/* Included after worker.c. Read the complete NVRAM snapshot while holding the
 * SAME operation lock used by the future settings writer and all mutations.
 * The reader's returned pointer may be reused by its very next call. */
static int wr_eoip_stored_dispatch(struct wr_eoip_worker *worker, const char *action,
    const char *(*read_value)(void *, const char *), void *context,
    int (*load_module)(void *), char *message, size_t size)
{
    static const char *keys[9] = {"enable", "autostart", "local", "remote", "id", "mtu", "keepalive", "retries", "bridge"};
    struct wr_eoip_state operation = {.fd = -1};
    char values[8][9][48], slots[8][2], key[32];
    char *args[82] = {"eoip-service", NULL};
    const char *master;
    unsigned slot, field, enabled;
    int result = WR_EOIP_WORKER_INVALID, applying;
    if (!worker || !worker->transport || !worker->directory || !message || !size || !read_value || !action ||
        (strcmp(action, "boot-stored") && strcmp(action, "apply-stored"))) return WR_EOIP_WORKER_USAGE;
    applying = !strcmp(action, "apply-stored");
    master = read_value(context, "eoip_enable");
    /* Default-off boot needs no runtime files. A concurrent enable queues its
     * own Apply notification; it cannot yield a mixed partially read table. */
    if (!applying && (!master || !strcmp(master, "0") || !*master)) {
        wr_eoip_worker_report(message, size, "boot disabled", -1);
        return WR_EOIP_WORKER_OK;
    }
    if (!wr_eoip_state_lock_named(worker->directory, &operation, "operation-lock")) {
        wr_eoip_worker_report(message, size, "operation busy or state directory unavailable", -1);
        return WR_EOIP_WORKER_REFUSED;
    }
    master = read_value(context, "eoip_enable");
    if (!master || !*master) master = "0";
    if (!wr_eoip_decimal(master, 1, &enabled)) {
        wr_eoip_worker_report(message, size, "master flag invalid", -1); goto done;
    }
    if (!enabled) {
        args[1] = "stop-table";
        if (applying) result = wr_eoip_worker_dispatch_unlocked(worker, 2, args, message, size);
        else { wr_eoip_worker_report(message, size, "boot disabled", -1); result = WR_EOIP_WORKER_OK; }
        goto done;
    }
    args[1] = applying ? "apply-table" : "boot-table";
    for (slot = 0; slot < 8; slot++) {
        slots[slot][0] = (char)('0' + slot); slots[slot][1] = 0;
        args[2 + slot * 10] = slots[slot];
        for (field = 0; field < 9; field++) {
            const char *value;
            size_t length;
            snprintf(key, sizeof(key), "eoip_slot%u_%s", slot, keys[field]);
            value = read_value(context, key);
            if (!value) value = "";
            length = strlen(value);
            if (length >= sizeof(values[slot][field])) {
                wr_eoip_worker_report(message, size, "stored value too long", (int)slot); goto done;
            }
            memcpy(values[slot][field], value, length + 1);
            args[3 + slot * 10 + field] = values[slot][field];
        }
    }
    args[1] = "validate-table";
    result = wr_eoip_worker_dispatch_unlocked(worker, 82, args, message, size);
    if (result != WR_EOIP_WORKER_OK) goto done;
    for (slot = 0; slot < 8; slot++) {
        unsigned on = 0, automatic = 0;
        wr_eoip_decimal(values[slot][0], 1, &on);
        wr_eoip_decimal(values[slot][1], 1, &automatic);
        if (on && (applying || automatic)) {
            if (load_module && !load_module(context)) {
                wr_eoip_worker_report(message, size, "module loading failed", -1);
                result = WR_EOIP_WORKER_UNCONFIRMED; goto done;
            }
            break;
        }
    }
    args[1] = applying ? "apply-table" : "boot-table";
    result = wr_eoip_worker_dispatch_unlocked(worker, 82, args, message, size);
done:
    wr_eoip_state_unlock(&operation);
    return result;
}
#endif
