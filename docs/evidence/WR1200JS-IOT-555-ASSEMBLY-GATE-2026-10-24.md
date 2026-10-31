# IoT optional candidate build: assembly gate before MIPS compile

Run [40071175138](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40071175138)
was dispatched with `boards=wr1200js` and `run_candidate_checks=true` for
commit `1ae24087f2baa821cb418f3ada583cd289e0313c`. The normal firmware
build and image checks preceded the isolated candidate step. The optional
step failed before target compilation with
`assemble-prepared-candidate.py: error: Candidate overlay shape changed;
review required`. The downstream `downloads` job failed because the build
job failed; it is not an independent compiler finding.

The fail-closed assembler expected 45 candidate source overlays and 31
original Git blobs. The reviewed TIM admission change added exactly
`ap/ap_nps.c` to both, so the current candidate has 46 overlays and 32
original blobs. The full-source lock inventory had already been updated for
that file in commit `1ae2408`; the assembler's separate inventory gate had
not. Its expected counts were updated without relaxing path, SHA-256, pinned
Git blob, overlap or merge validation.

Local assembly against pinned `c25283e915a2a00a763774dd255b14aff997285e`
and the existing prepared driver completed into
`../iot-merged-tim-gate-v2-20261024/`: 46 candidate paths and five
prepared-source merges. The generated manifest reports
`target_compiled=false`, `production_installed=false`, and
`runtime_verified=false`. Python syntax and `git diff --check` passed.
This verifies the assembly gate only. A new optional MIPS compilation is
required; no firmware or router state was changed by this local fix.
