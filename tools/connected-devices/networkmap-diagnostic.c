/* One-shot device diagnostic using the production source collector.
 * No client identifiers are emitted. No service or NVRAM changes are made.
 * The collector briefly takes a nonblocking POSIX lock, as httpd does. */
#include "source-collector.h"
#include <signal.h>
#ifndef WR_DIAGNOSTIC_SOURCE
#define WR_DIAGNOSTIC_SOURCE "/tmp/static_ip.inf"
#endif
#ifndef WR_DIAGNOSTIC_LOCK
#define WR_DIAGNOSTIC_LOCK "/var/lock/networkmap.lock"
#endif
int main(int argc, char **argv)
{
    struct wr_device_snapshot snapshot;
    struct wr_device_source_paths paths = {WR_DIAGNOSTIC_SOURCE, WR_DIAGNOSTIC_LOCK};
    struct stat existing;
    int ok;
    (void)argv;
    if (argc != 1) return 2;
    /* Do not create a missing production lock as a side effect of diagnosis. */
    if (lstat(paths.lock, &existing) || !S_ISREG(existing.st_mode)) {
        puts("{\"networkmap\":\"unavailable\",\"preflight\":\"lock_missing_or_not_regular\"}");
        return 1;
    }
    alarm(3);
    ok = wr_device_networkmap_collect(&snapshot, &paths);
    alarm(0);
    if (!ok) {
        puts("{\"networkmap\":\"unavailable\",\"preflight\":\"passed\"}");
        return 1;
    }
    printf("{\"networkmap\":\"collected\",\"records\":%u,\"invalid\":%u,\"truncated\":%s}\n",
           snapshot.count, snapshot.invalid, snapshot.truncated ? "true" : "false");
    return 0;
}
