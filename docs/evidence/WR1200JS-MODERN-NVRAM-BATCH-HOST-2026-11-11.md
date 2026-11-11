# Isolated NVRAM batch prototype — 2026-11-11

Status: HOST VERIFIED prototype only; not installed, no ioctl, no production
Apply activation, no kernel/target/image/device acceptance.

Pinned source revision: c25283e915a2a00a763774dd255b14aff997285e.
The fixture extracts actual hash, get/set, tuple allocator/free from
`trunk/linux-4.4.x/drivers/nvram/{nvram.c,nvram_linux.c}`.
Common SHA256: c2d8ff085f9be3cc0aad76f5b7df1700607c8e429dc8731d8305c8deab4d4e6b.
Linux SHA256: 5bdfa51add776cfe46eabd5c328859d74822220e7772335d08e21b91750190c1.
Header SHA256: 411b381cdff5d6fea5fda76510e7a5dacff591dd067ce47c3cc3e225ae42b33e.

The candidate holds existing nvram_lock across comparisons, staging and
publication. It stages fresh tuples and append-only values; it publishes only
after every allocation succeeds. Failure frees staged tuples, wipes the newly
appended tail and restores its offset. Existing values remain untouched.
It does not compact, commit flash, notify services or change ACK handling.

Reproduce:
```
PYTHONDONTWRITEBYTECODE=1 python3 tools/webui-preview/check_nvram_batch_core.py /home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar
```

GCC warnings-as-errors, ASan/UBSan: PASS. Tests inject every allocation failure
for four and sixteen changed keys; the sixteen names collide in one hash
bucket. They verify no partial updates, offset/heap restoration, successful
collision-chain replacement, stale expectation rejection before allocation,
no-op, capacity refusal, duplicate/count rejection, check-only and insertion,
and retention of a borrowed previous value after successful replacement.
Host heap and lock-depth substitutes do not prove real concurrency, kernel
latency, user-copy safety or borrowed-pointer lifetime after later legacy
compaction. Missing and empty compare equally by current prototype policy.

Next: define bounded pointer-free ABI and admission/ownership policy, prove
compatibility with legacy writers and commit/notification sequencing, install
only into an isolated kernel candidate and obtain target checks before any
production use. Whole request atomicity and durable flash success remain open.

Cleanup: successful final run inventoried and auto-removed 109707 bytes of
owned source/executable scratch; directory absence asserted. No firmware,
archive, source input or unrelated work removed. CI99442963851036 and
CI99542965079106 freshly report completed/success; artifact acceptance pending.
