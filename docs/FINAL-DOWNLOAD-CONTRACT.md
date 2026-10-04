# Final firmware download contract

User-confirmed 2026-10-04: at project delivery, a successful firmware build exposes exactly one user-download ZIP artifact. For WR1200JS it contains exactly the firmware TRX and matching central requested build config, with no logs, reports, toolchain data or duplicate download bundles. Build reports and checksums can be displayed in the job summary/logs.

For future multi-router runs, preserve the already requested multi-board build capability: the single outer ZIP contains a clearly named per-board directory with that board's TRX and config, and no diagnostic files. Unverified reference profiles remain excluded from automatic builds.

Current development builds retain evidence artifacts while integration is incomplete. At final delivery, collect necessary diagnostics in job logs/summary, remove duplicate uploads and temporary candidate artifacts from the normal delivery workflow, and verify the Actions artifact list contains only the intended archive. Do not erase historical evidence to implement this requirement. A failed selected build must not be advertised as complete firmware delivery.

Current evidence: run37205898200 final artifact11305311394 (WR1200JS_4.4.198.9-100) independently downloaded and inspected: exactly WR1200JS_4.4.198.9-100.trx and wr1200js.config. See FINAL-ZIP-37205898200.json. This confirms the separate minimal artifact exists; it does NOT satisfy the single-artifact requirement, because the development run also uploaded diagnostics and a common bundle. No runtime verification is inferred.

Implementation location: .github/workflows/build-multiple-boards.yml firmware-zip job currently uses tools/stage-firmware-download.py and already stages only TRX/config. Its downloads job creates the extra common diagnostic bundle; build-padavan-4.4-wr1200js.yml also uploads source/build evidence. Consolidate these for final normal delivery after feature acceptance. Preserve source/config matching, successful-build gates and archive-content checks.
