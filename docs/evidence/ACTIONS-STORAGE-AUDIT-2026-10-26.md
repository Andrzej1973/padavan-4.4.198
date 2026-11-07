# GitHub Actions history and storage — 2026-10-26

Repository `Andrzej1973/padavan-4.4.198` is public. GitHub's repository API
reported 1,307 workflow runs and 8,306 artifact records. The run count is
history, not a charge by itself. A sample of the newest 100 artifact records
totaled 146,783,861 bytes; this is not a repository-wide storage total.

Before cleanup the cache API listed 65 entries, 10,566,459,685 bytes:
44 WR1200JS `ccache` entries (10,565,975,112 bytes), 20 tiny agent-monitor
entries and one nim-monitor entry. The 44 compiler caches used a unique
run ID in each key. Thirty oldest WR1200JS compiler caches, from run
`40073309681` through `40260205702`, were deleted by exact cache ID after
checking the inventory boundary. These represented 7,117,485,674 bytes.
The cache-list API then confirmed 35 entries, 3,448,974,011 bytes, including
14 recent WR1200JS compiler caches. No workflow runs, artifacts, source files
or router state were deleted. The separate cache-usage endpoint still showed
its prior count immediately afterward, so the cache-list response is the
post-deletion verification and the usage aggregate may lag.

Local workflow change after this audit: use one UTC-day cache key rather than
one cache key per run; retain the old-key prefix as a restore fallback.
The exact-hit path skips save. YAML and key-condition static checks passed;
the change has not yet run in CI. The per-job `CCACHE_MAXSIZE=2G` remains
unchanged. This limits future duplicate cache entries; it does not replace
firmware/image verification.

The two successful isolated Mi Mini radio checks and their limits are retained
in `docs/evidence/MI-MINI-RADIO-PROBE-CI-2026-10-26.md`. Their diagnostic
artifacts had already expired before this cleanup.

Billing limitation: this executor's `gh` token could not read the personal
billing usage endpoint (HTTP 404; `user` scope requested). GitHub's published
rules say standard hosted runners in public repositories are free, while
artifact/cache storage has separate allowances. Actual account charges or
budget settings were not verified here.
