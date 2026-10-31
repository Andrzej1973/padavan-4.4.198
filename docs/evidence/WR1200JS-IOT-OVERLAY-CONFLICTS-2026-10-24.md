# IoT candidate versus prepared MT7603 source — 2026-10-24

The complete IoT candidate from ABI run 40021678711 is pinned to upstream
MT7603 revision `c25283e915a2a00a763774dd255b14aff997285e`. Its manifest
records 45 driver-directory overlay paths and 31 original Git blobs. The
firmware workflow separately prepares Band Steering and RSSI source changes
before building the kernel. Copying the candidate over that prepared source
would replace overlapping edits without a reviewed merge.

`tools/iot/check-overlay-conflicts.py` verifies candidate SHA-256 records and
compares the recorded original blobs with a supplied prepared driver tree.
It only reads source files and fails closed when an original is missing, an
original was modified, or a new candidate path collides with a different file.

Local checks against the downloaded #542 ABI artifact:

| Input tree | Pristine originals | Modified originals | Missing originals | New paths absent | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Pinned upstream MT7603 | 31 | 0 | 0 | 14 | Pass |
| ABI `rssi-query-source` fixture | 0 | 4 | 27 | 14 | Conflict |

The four modified paths visible in that *partial fixture* are `ap/ap.c`,
`ap/ap_cfg.c`, `common/rtmp_init.c`, and `include/rtmp.h`. The fixture does not
contain the whole driver, so its 27 missing originals are not evidence about
the finished firmware source.

Next, the verified full upstream source archive was unpacked only in sibling
scratch directory `iot-source-prepared-20261024`. All 20 Band Steering source
preparation stages that precede its ABI probe and all five RSSI preparation
scripts completed there, in the same order as the firmware workflow. The
candidate gate found 26 pristine original files, five modified originals,
zero missing originals, and 14 absent new candidate paths. It exited 1. The
five paths requiring a deliberate merge are `ap/ap.c`, `ap/ap_cfg.c`,
`common/rtmp_init.c`, `hw_ctrl/cmm_asic_mt.c`, and `include/rtmp.h`.

The target compiler was unavailable locally, so the Band Steering ABI probe,
layout extraction, and userspace package registration were not run. Source
inspection of those remaining scripts shows that they read the prepared driver
and write probe/user-package files, rather than modifying the MT7603 driver.
This supports the five-path overlap for the workflow's driver preparation
sequence, but does not prove the final built source or target compilation.

An isolated three-way `git merge-file` probe used pinned upstream as the base,
the prepared source as one side, and the IoT candidate as the other. Windows
Python text writes had converted the five prepared files to CRLF, so the first
probe produced spurious whole-file conflicts. After normalizing *copies* to
LF, four paths merged without text conflicts: `ap/ap.c`, `ap/ap_cfg.c`,
`hw_ctrl/cmm_asic_mt.c`, and `include/rtmp.h`. `common/rtmp_init.c` has one real
same-anchor conflict immediately before `*ppAdapter = (VOID *)pAd`: RSSI
initializes `wr_rssi_birth` and `wr_rssi_observer`; IoT initializes its
transition lock, radio transition, generation and interface references.
Both sequences must be retained before adapter publication. The probe is in
`iot-merge-probe-lf-20261024` beside the repository. Automatic text merging
does not establish semantic correctness or compilation.

Evidence JSON is in the sibling workspace files
`iot-pristine-overlay-check-20261024.json` and
`iot-rssi-query-overlay-conflicts-v2-20261024.json`, and
`iot-prepared-overlay-conflicts-20261024.json`. The pristine check exited
0; both prepared-source checks exited 1 as designed. `python -m py_compile`
passed for the checker. No candidate file was installed into the production
driver, and no target compile, image, or router check was claimed here.

Next: review the four clean text merges, resolve the one initialization
conflict with both sequences retained, and inspect the whole candidate source.
Then target-compile the merged candidate in
an isolated copy with the exact WR1200JS effective driver configuration. Do
not use a wholesale overlay as a target-compile shortcut.

## Isolated merged candidate staged

`tools/iot/assemble-prepared-candidate.py` now assembles a separate full
MT7603 driver tree only when the pinned source blobs, candidate SHA-256 file
records, 45 overlay paths and the exact five modified prepared paths match.
It uses three-way text merges for those five files and resolves the single
`common/rtmp_init.c` conflict by retaining RSSI initialization followed by
IoT transition/reference initialization before adapter publication. Any
changed or additional conflict aborts rather than choosing a side.

The local run wrote `iot-merged-candidate-20261024` beside the repository and
its SHA-256 manifest. All 45 recorded output hashes match; no `<<<<<<<`
markers remain; the RSSI query/identity and IoT transition markers are present.
The manifest records `target_compiled=false`, `production_installed=false`,
and `runtime_verified=false`. This source check does not establish C type
compatibility, Kbuild selection, radio behavior, or safe IoT activation.

Next: inspect the merged driver against both input sides, then target-compile
it with the exact WR1200JS kernel configuration in an isolated build. The
candidate must remain outside the production image until the compile and
subsequent lifecycle/rollback gates pass.

## CI probe prepared

The current local candidate generator was rerun from the pinned source. Its
raw files differed from the Linux #542 artifact only because Windows Python
text writes produced CRLF; normalizing source text to LF yielded the same
content hashes. The merge assembler now normalizes its candidate merge input
and its staged output. A second full assembly from the *current* local tools
matched all 45 staged output hashes from the #542-based assembly.

An optional step was added to the WR1200JS reusable firmware workflow. It
runs only with `run_candidate_checks=true`, after successful baseline firmware
build and isolated Band Steering driver compilation. It recreates the pinned
candidate from Git history, merges it into the isolated prepared kernel copy,
checks staged hashes, and attempts MIPS `vmlinux modules` compilation. The
normal firmware image remains based on the untouched production source tree.
The step's shell syntax passed `bash -n` locally. Commit `5a09fc7` was pushed
to the PR branch. Baseline firmware #543 and the matching ABI run passed.
After checking that this branch had no queued or running duplicate, a single
manual `run_candidate_checks=true` run was dispatched as `40046513315`.
It completed with failure after the baseline image had been produced. The
`iot-merged-driver-probe` artifact from build #544 contains the isolated
compiler log. Its first error is `-Werror=misleading-indentation` in
`ap/ap_cfg.c:14639-14642`, in `Set_BcnStateCtrl_Proc`: the candidate added
`if (changed)` but left the inherited `return TRUE` with an eight-space
indent. The candidate compiler stopped at that warning; the downloads job
then failed because the selected optional build failed. This is a candidate
source error, not evidence that the baseline firmware image failed to build.

The generator now aligns that return with the function body. A fresh local
candidate and prepared-source merge completed; 44 of 45 merged source hashes
were unchanged, and the only changed path is `ap/ap_cfg.c`. The generated
function shows the return at four spaces after the conditional log. Python
syntax and `git diff --check` passed. Target compilation of this correction
remains unverified until the next isolated CI run; production IoT and router
runtime remain unverified.

## Second isolated target-compile blocker

Run `40048878570` on `236dedb` advanced past the previous debug-setter error
but stopped compiling `common/cmm_mac_pci.c:2740`. The candidate used
`GET_BCNRING_FREENO(pAd)` as an expression; the pinned vendor macro at
`include/iface/rtmp_inf_pcirbs.h:109-113` includes a trailing semicolon,
so the compiler reports `expected ')' before ';' token`. Its artifact
`iot-merged-driver-probe` is saved at `../iot-merged-probe-546/`.

The candidate generator now checks the ring-index zero-free condition
directly while holding `BcnRingLock`. For `BCN_RING_SIZE=20`, an exhaustive
check of all 400 valid index pairs confirmed equivalence to the vendor
macro's zero result. A fresh candidate and five-file prepared-source merge
completed; only `common/cmm_mac_pci.c` differs among the 45 staged files.
This is local source evidence, not a target compile or runtime result.

## Isolated MIPS target compile completed

Run `40051068385` on commit `22df59a` completed successfully with
`run_candidate_checks=true`. Its `iot-merged-driver-probe` artifact was
downloaded to `../iot-merged-probe-550/`. The 45 merged driver-file SHA-256
values match the fresh local prepared-source assembly exactly. The isolated
kernel built `vmlinux modules`, and the artifact contains a 5,106,508-byte
`mt76x3_ap.ko` identified by `readelf` as ELF32 little-endian MIPS relocatable
code. The workflow also checked its effective `.config` hash before and
after this compile. The build log reports one `modpost` section-mismatch
warning without details; this has not yet been attributed to the candidate.
The same run's preceding isolated Band Steering driver build artifact,
downloaded to `../band-steering-probe-550/`, contains the same one-section
`modpost` warning before the IoT candidate was copied. Both artifacts have
the same effective kernel `.config` SHA-256
`FA047C0252B38D5E9525DBBD80CD1EF8CD4564D01B384EDB5D861C200177AAA9`.
The warning therefore predates the candidate overlay in this run; its
underlying section reference has not been diagnosed here.

The target `merged-capacity.json` reports complete Kbuild/directive evidence
for all nine source units and 20 source-text `BcnRingLock` sites. Nineteen
survive preprocessing: 10 SEM and 9 IRQ; the `RTMPFreeTxRxRingMemory` SEM site
is inactive. `MULTI_CORE_SUPPORT` is false in every unit, so both lock forms
expand to the BH wrapper in this particular target configuration. This
establishes compilation and the effective macro forms; it does not prove
all callback contexts, selective IoT BSS teardown, production installation,
or device runtime. The candidate manifest still correctly says
`target_compiled=false` because that source manifest was generated before
CI compiled it; the external CI artifact is the compile evidence.

Source trace for two asynchronous owners: `os/linux/rt_rbus_pci_drv.c`
initializes `bcn_dma_done_task` with `bcn_dma_done_tasklet` at line 69; that
callback calls `RTMPHandleBcnDmaDoneInterrupt` at line 629, where the
candidate's SEM-form `BcnRingLock` acquisition is compiled. The same file
initializes `rx_done_task` at line 62; its callback calls
`rtmp_rx_done_handle`, which reaches `GetPacketFromRxRing` and
`parse_rx_packet_type` in `common/cmm_data_pci.c`, then
`ParseTxSPacket` in `common/cmm_data.c:611` and the candidate's
IRQ-form `BcnTxSHandler`. `include/os/rt_linux_cmm.h` maps both forms to
`RtmpOsSpinLockBh` without `MULTI_CORE_SUPPORT`; `rt_linux.c:3383` and
`include/os/rt_linux.h:367-369` map that wrapper to `spin_lock_bh`.
The isolated target `.config` does not set
`CONFIG_MT7603E_WIFI_WORK_QUEUE_BH`; the MT7603 AP Makefile adds
`-DWORKQUEUE_BH` only when that option is `y` (line 606-608). Thus these
two callbacks use the tasklet branch in the reviewed target build.
This traces these two callback chains only. All other lock owners, nested
lock ordering, and safe teardown
still require review; neither compile success nor identical lock macros
establishes full production safety.

The MT7603 candidate has a separate TIM-packet submission chain:
`ap/ap_nps.c:51-81` calls `HAL_KickOutMgmtTx` on `Q_IDX_BCN` under
`BcnRingLock`; `APMakeBssTimFrame` calls it at line 243; and
`APMakeAllTimFrame` calls the former at line 280. The assembled candidate's
`common/cmm_data_pci.c:1520-1526` defines `RTMPHandlePreTTTTInterrupt`,
which calls `APMakeAllTimFrame` in AP mode. The private `TimEnable` setter
at `ap/ap_cfg.c:14469-14534` can allocate a TIM packet and enable the
relevant hardware interrupt bits. The successful isolated target module in
run `40051068385` contains all four functions; `readelf -rW` shows the
`R_MIPS_26` call relocation from `RTMPHandlePreTTTTInterrupt` at offset
`0x0000b318` to `APMakeAllTimFrame`. No direct call to
`RTMPHandlePreTTTTInterrupt` was found in the assembled candidate's C source
or as an `R_MIPS_26` module relocation. The module's sole `R_MIPS_32`
reference to this handler is in `.rel.pdr`, a MIPS procedure descriptor/debug
section, not an executable interrupt dispatch table; it has no `__ksymtab`
export. In `os/linux/rt_rbus_pci_drv.c:1627-1640`, the reviewed
`WF_MAC_INT_4` branch reads `HWISR4` and masks active `HWIER4` bits, but
neither calls nor schedules the PreTTTT handler. These exact source/module
observations exclude a direct dispatch of TIM frames by this branch in the
successful isolated candidate build; they do not establish behavior under
another driver build or an unseen indirect entry. The first symbol search
over the narrower pinned reference tree missed `common/cmm_data_pci.c`;
the assembled candidate and linked module correct that search's scope. Keep
`beacon_ring_admission_atomic=false` for the remaining active producers and
teardown gaps, and recheck this exclusion against the final production
module before changing the gate.

Manual run `40054121188` on `5da2e60` completed successfully with
`run_candidate_checks=true`. Its `iot-merged-driver-probe` artifact was
downloaded to `../iot-merged-probe-550-guard/`. The new fail-closed guard
executed after the isolated `vmlinux modules` build: the report has nine
complete Kbuild units, all unit flags and site activity available, 20 source
sites, 19 active sites (10 SEM, 9 IRQ), and no unit with
`MULTI_CORE_SUPPORT`. The `merged-capacity.json` and
`merged-source-manifest.json` SHA-256 hashes match the prior successful
candidate artifact exactly. The new `mt76x3_ap.ko` is 5,106,508 bytes,
ELF32 little-endian MIPS relocatable, SHA-256
`945D009F25D25853717F42C148935CF8F45A4AC24B1BBB1F0191961F6D795BA0`.
Its hash differs from the earlier module build despite identical source and
capacity reports; no byte-for-byte module reproducibility claim is made.
The same one `modpost` section-mismatch warning remains. This proves the
guard executes on the target candidate compile; it does not promote the
candidate to production or prove safe selective IoT BSS teardown.
