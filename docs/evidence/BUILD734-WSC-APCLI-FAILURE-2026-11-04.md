# Optional 734: WSC APCLI compile failure

Run 41768450746 on fd76301e failed in the full WSC feature module:
ap/apcli_sync.c:1368/1525 uses bHasWscIe with both declarations commented out.
Original job 126372326486 and artifact 13294353568 confirm the error.
Monitor 41770633873/artifact 13295010550 identifies the step but deployed
prefix-only parsing misses the cause. Existing branch suffix parser passes
the added exact-error regression; no duplicate parser fix or main mutation.
Isolated feature preparer restores FALSE-initialized per-call WSC_AP_SUPPORT
locals in both probe builders; baseline and production source stay unchanged.
Real pinned input transformation and drift rejection pass; target rerun due.
Baseline MIPS module independently verified: 5574532 bytes, SHA256
4496d406d79d8455e5b4d0d951a270094d9254c3cda2050892fba00850a654b8.
Reload-mode ASIC TU passed (1096-byte checked-off function), not full reload
module, firmware shutdown or runtime acceptance. Full WSC remains incomplete.
Monitor scratch executable/cache removed; artifacts read in memory, no archive
retained. Preserved unfinished source inputs and owner references. Router untouched.

