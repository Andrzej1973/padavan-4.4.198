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
