# WR1200JS compiler cache — 2026-11-11

The standard and optional lanes share each Ubuntu/toolchain rolling cache prefix.
Keys include run/attempt for immutable Actions snapshots; restore prefix excludes
run/attempt so subsequent runs can reuse the newest snapshot. Existing v4 host
separation is retained during Ubuntu comparison. v3 was not imported into the
new host baseline;1016/1017 cold cache hit rates were14.72% and15.34% respectively.
Optional1019 has final warm statistics:10390/10435 cacheable calls hit(99.57%),
45 misses.1018 remains active; its final rate is not yet available.
The Actions cache API shows corresponding v4 entries accessed near their start.

Keep compiler_check=content and normal source/header freshness validation; do
not raise a hit rate using sloppiness, frozen build identity or skipped rebuilds.
The2G local capacity is not the measured bottleneck (about0.16GB standard cache).
Linking, configure probes and unsupported commands do not become cache hits by
increasing that capacity. Current standard figures are evidence of cold starts,
not proof that warm caching is ineffective.

The former success-only save lost valid cache growth when a later runtime/image
check failed. Save now remains after the isolated candidates and can run after
build/test failure, provided cache restore/setup succeeded and firmware execution
was reached; cancelled jobs and skipped builds do not save. Compiler failures
are not cached as successful objects. Real local fixture confirms repeat-hit,
changed-source output change, failed compile and original-source cache recovery.
This is compiler-cache correctness evidence, not measured CI speed improvement.

`compiler-cache-statistics` now preserves verbose miss/error reasons and raw
counter IDs. It does not change the image's acceptance result. The99.57% measured warm rate does not justify further cache-key or capacity
changes merely to seek100%.1019 failed a separate host fixture warning about
uninitialized iot_dev; these stats do not prove merged target module success.
Compare final1018 stats when available. Do not pool host caches or weaken validation merely for a higher
percentage. No diagnostic rebuild is required for this cache audit.

Evidence: `evidence/WR1200JS-COMPILER-CACHE-AUDIT-2026-11-11.json`.
References: https://ccache.dev/manual/4.9.1.html#_cache_statistics and
https://github.com/actions/cache/tree/main/save .

Observed verification: failed optional1023 at60072c1 produced cache key
wr1200js-ccache-v4-ubuntu-24.04-source-43065290017-1 (120582939B, created
2026-11-11T17:20:45Z). This confirms save-after-late-failure on an actual runner;
the failure remains a failure and is not hidden by cache persistence.
