# ABI599 Linux replay - 2026-10-31

## 2026-10-31 Sol: complete Linux candidate replay and stale audit repair

Replayed the CI source preparation from pinned c25283e with early idle-aging/grant-readback/main-bss changes, then current recovery, full overlay, 74-stage peer chain and prepared RSSI merge. Assembly passed in /tmp/wr-abi599-full.vEmGGs. The following scheduler audit initially failed because it expected untyped pAd access, while the merged PCI probe correctly casts void * to PRTMP_ADAPTER. Updated only that audit assertion to require exactly one typed auxiliary work join. Positive actual-candidate audit and negative untyped/missing-join checks pass; scratch source restored byte-for-byte.

Actual merged RSSI deletion and extracted PCI probe work joins compile/run with GCC -Wall -Wextra -Werror and AddressSanitizer/UBSan. git diff --check passes. Full MIPS driver Kbuild, image and runtime acceptance remain unverified. No router mutation, commit or push. Next: target/feature compilation and preserve external archive evidence; do not delete Windows original.

Changed implementation: tools/iot/audit-aux-family-retry-scheduler.py, one assertion. Workflow's previously staged pristine extraction fix remains local. Audit is invoked against the assembled candidate by .github/workflows/band-steering-abi.yml; it must inspect the final typed PCI probe expression, not the pre-merge form.

Evidence scope: source composition and host fixtures, not actual kernel work cancellation, DMA quiescence, whole-driver MIPS compilation or device behavior. Vendor bodies/kernel cancellation are injected in the fixtures. Candidate and receipts are local temporary evidence, not production-installed code.

External preservation remains active: Windows tar PID 13756 to D:/Padavan-preservation-20261031/workspace-active-materials.tar. Last observed live, empty stderr. Incomplete G: archive and original source retained. Completion/content verification still required before deletion.

## 2026-10-31 Sol: seven target MIPS fixture objects compiled

Downloaded the CI-pinned toolchain to user cache; SHA256 de412846a5d057faf132b2463aa29c24f77c79c744f4181c1a287bbeaf1d7256 matched. GCC 10.5.0 compiled seven MIPS32r2 little-endian objects with -Wall -Wextra -Werror: merged peer RSSI deletion, actual PCI probe work joins, WCID FIFO retirement, UAPSD retirement, successor ledger, close and post-open. Successor extracted host checks also passed. Sizes/hashes in docs/evidence/WR1200JS-ABI599-MIPS-OBJECTS-2026-10-31.json. This verifies fixture objects, NOT whole-driver Kbuild, kernel ABI, firmware image or device acceptance. Those remain next. No full local firmware build, commit/push or router changes.


## Full-driver gate revalidated from live CI

GitHub run 41213029201 (firmware #649, df562280) completed successfully. Its actual job steps show Probe effective IoT third-BSS radio capacity: success, Compile isolated merged IoT MT7603 candidate: skipped, Upload isolated merged IoT driver diagnostics: skipped. Therefore this run provides no whole peer82 driver compilation evidence. ABI run 41213029208 remains failed at the already localized preparation error; the local repair is not published.

The existing full-driver route is .github/workflows/build-padavan-4.4-wr1200js.yml, step Compile isolated merged IoT MT7603 candidate. It requires run_candidate_checks=true, candidate_scope=iot, iot_candidate_variant=peer82. Entry workflow: build-multiple-boards.yml. It creates an isolated kernel from the built baseline, merges the candidate, runs vmlinux/modules, checks config invariance, capacity and MIPS ELF/symbols, then emits target-compile-result.json. It does not install the candidate into the production image.

Next execution order: preserve the local repairs; review/publish only when authorized; ensure no run is active for the same ref/SHA; run the existing isolated peer82 check on that exact revision. Require iot-merged-driver-probe target-compile-result.json and module/config/source provenance. A green ordinary firmware run with this step skipped cannot close the gate. Feature combinations, lifetime/DMA quiescence, production integration and device acceptance remain separate open requirements.

Local full-driver compilation is deferred while the external archive is the resource-heavy operation, following the 8-GB host constraint. Seven local cross-compiled fixture objects are recorded separately and do not substitute for Kbuild.
