# INITIAL routed shutdown integration candidate

Status: package installed in tools/iot; full postintegration host suite PASS.
Production route remains unarmed; target and device verification pending.
Installed sources and permanent tests: `tools/iot/initial-shutdown-owner.h`,
`initial-off.c`, `rc-initial-stop.c`, `rc-physical-stop.c`, `rc-backend.c`,
and `check-initial-shutdown-*.py`. The local preparation package remains under
`.scratch/initial-shutdown-package/integration-manifest.json`.
Evidence: `docs/evidence/WR1200JS-INITIAL-SHUTDOWN-PACKAGE-HOST-2026-11-16.json`.

## Ownership and call chain

`rc-normal-shutdown.c` retains the first routed TERM/QUIT and creates one private
OFF envelope. `rc-physical-stop.c:physical_begin` selects INITIAL only for routed
shutdown with actual `wr_iot_rc_boot_idle()`. ACTIVE continues through existing
quiesce/CLOSE; absence of a CLOSE is not proof of INITIAL.

`initial-shutdown-owner.h` binds process PID, original signal and the exact live
outer fence. It checks routing armed, pending/requested equality, no replay and
no competing ON/OFF owner. It never changes the signal state.

`wr_iot_rc_backend_initial_shutdown_prepare` acquires the existing service guard,
checks boot idle before/after fresh INITIAL observation, and only then publishes
the candidate witness. Ordinary observation still rejects pending signals.
`rc-initial-stop.c` drains auth and six AUX interfaces before requesting a fresh
exact ARM. Its ordinary and shutdown entry points remain distinct. The existing
physical session owns command uncertainty, one possible Main DOWN, completion
and typed RELEASE; the new route supplies no ACK or DMA shortcut.

Final release validates the exact private OFF envelope and typed INITIAL RELEASE
(or the existing legacy CLOSE release). Failed signal-mask restoration retains
the physical and normal owner. After successful restoration, private owners are
cleared before routing is disarmed and the original signal is replayed once.

## Verification and integration gates

Host fixtures cover real TERM/QUIT, first-signal retention, foreign owner refusal,
fresh observation, auth/AUX ordering, uncertain ARM, one DOWN, exact RELEASE,
wrong OFF envelope, failed final unmask, private cleanup before stock replay,
and ordinary INITIAL / legacy ACTIVE compatibility. Driver/network/NVRAM
operations remain injected actors. These are not hardware completion results.

Public headers compile independently from declared staged dependencies. Runtime
staging compiles WPIQ client/session/controller without repository include
fallback. Candidate target-link checks require five new shutdown API symbols.
The presence of these checks does not constitute a MIPS build result.

Baseline full regression passed with all 1818 inputs unchanged; its log, result
and input hashes are preserved under the evidence stem
`WR1200JS-INITIAL-REOPEN-FULL-HOST-PASS-2026-11-16`. The reviewed package is
installed and all eight focused checks are registered in the existing suite.
Installed full regression passed with all 1828 inputs unchanged. Result, log
and input hashes: `WR1200JS-INITIAL-SHUTDOWN-FULL-HOST-PASS-2026-11-16`.
Target compilation and independent final-image verification remain pending.
Production-route admission and physical device acceptance remain separate.
No ACK reuse/protection, firmware protocol or global DMA/queue state changes.
