# Build #495 KVR fixture repair — 2026-10-20

Run 39449320716, head 307f7c9, failed before firmware compilation in the shared
Wi-Fi preparation step. The original build-job log (118719679348) was downloaded
and processed with the existing local Nim build_log utility. Its first causal
compiler errors were an implicit wr_profile_wlan_get_int declaration and an
unused nvram_wlan_get_int mock, both under -Werror.

An earlier source adapter rewrites the generated configuration getter to the
coordinated profile-snapshot getter. The new KVR emitter test hardcoded the
original NVRAM getter and therefore could not compile the real adapted block.
The production KVR duplicate-record transform itself was not the failing code.

The fixture now extracts the getter from the actual transformed KVR block,
requires one consistent name from an explicit two-name allowlist, and stubs
that getter. Unknown or mixed getters are rejected instead of disabling
compiler warnings. The local actual-C emitter regression passes 16 combinations
for the pinned getter and 16 for the adapted getter. This tests the getter
variants; it is not execution of the whole preparation pipeline or firmware.
Source-drift/repeated-preparation guards and -Wall/-Wextra/-Werror remain active.

Later Preserve EoIP image checks/downloads failures were consequences of the
precompile failure and absent image artifacts. Generic IMQ patch-reject text in
the monitor excerpt was not the first causal error in this job.

The next CI run must prove the complete preparation sequence and final image.
No router configuration, radio, service, reboot or flash action was performed.
