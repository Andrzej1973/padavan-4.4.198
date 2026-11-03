# Isolated poll join target evidence

GitHub run 41683127201 completed successfully for repository revision
`5d14aee43298d541042159d4decf05cd3a1b1b05`, candidate `peer82`.
Artifact `iot-merged-driver-probe` ID 13254659102 was downloaded into memory;
no archive or extracted build tree was retained locally.

Independently read `mt76x3_ap.ko`: 5,572,464 bytes, SHA256
`0f5fe1243b2669f15e65607ea3879fc73978a7624cd9e4ee2261822872232a61`.
Size and digest match `target-compile-result.json`. ELF identification is
32-bit, little-endian, relocatable, machine 8 (MIPS).
The report records KTHREAD enabled; OS_ABL, PM, timer task and WSC disabled.
This does not establish those other feature combinations.

This proves isolated target compilation, not production installation,
ordinary ndo integration, hardware quiescence or router runtime acceptance.
The report explicitly marks production_installed and runtime_verified false.

Standard firmware run 41683200467 and ABI run 41683200444 completed
successfully for `c363e1e036e0ffffe5d4a7c03378f4650d355e0b`.
After checking existing runs and remote SHA, optional run 41686992058 was
dispatched for that exact revision: boards=wr1200js,
run_candidate_checks=true, candidate_scope=iot, iot_candidate_variant=peer82.
It was confirmed in_progress; its result is not yet acceptance evidence.

## Completed handoff target verification

Run 41686992058 subsequently completed successfully on c363e1e0.
Independently downloaded artifact 13257692154 into memory and verified
`mt76x3_ap.ko`: 5,573,188 bytes, SHA256
`885b84731b1c4123fa166fd576ffac9a227cf32ac9413d953adf2ae0fb4f1ae2`.
Both match its metadata; ELF class/data/machine identify 32-bit little-endian
MIPS. Artifact includes installed caller and handoff fixture executables and
the submission-candidate manifest. The same feature limitations apply:
KTHREAD enabled, OS_ABL/PM/timer task/WSC disabled. Production installation
and runtime verification remain explicitly false. No archive retained.

Standard 41687673550 and ABI 41687673214 succeeded on
`90255eb84a5bfa65d50acee7d982b2ed294ea6f3`. Optional 41694908263 was then
submitted for that revision with the same peer82/iot inputs, to exercise the
new combined installed owner/caller host suite and target build in CI.
