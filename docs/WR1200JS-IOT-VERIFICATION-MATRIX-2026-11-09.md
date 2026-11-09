# WR1200JS IoT verification matrix — 2026-11-09

Source checkpoint: `5a3caacbdd6daf64e9ac4354a291ecc9a67788ab`.
IoT implementation is incomplete. No device acceptance or production activation
is claimed. Older successful runs prove only their exact recorded source.

| Requirement | Evidence now | Remaining acceptance |
| --- | --- | --- |
| Cold reservation of ra2, default OFF | Isolated precreated profile/driver implementation and host checks | Production RC integration, final image and device boot |
| Runtime OPEN without physical restart/scan | Isolated owner API and bounded host-publication receipt; optional965 compiled source232c4a6 | Physical Main/Guest continuity and no-scan trace; current source CI |
| CLOSE ownership/lifetime | Actual CLOSE target TU compiled in965; checked reference retirement | Endpoint integration and RF/FIFO/no-future-TxS proof |
| Reopen after CLOSE | Fenced; stale-PID negative witness exists | Proven per-BSS drain/report boundary or unique echoed lifetime identity |
| MCU ACK reuse | Stale protection retained; finite retired-ID budget understood | E1/E2 ROM reply lifetime/epoch contract; safe reuse not proved |
| Dedicated bridge/subnet/DHCP/DNS/firewall | Candidate RC objects, host packet/parser/transaction checks | Real activation backend, full RC link, target DHCP/DNS transactions and device isolation |
| IPv6 policy | Host firewall checks enforce DROP | Final integrated image and real IPv6 traffic validation |
| Shutdown and recovery |843f removes configuration bypass;1c retains normal shutdown fence during RECOVERY; host regressions pass | Strong controller binding, production shutdown integration and target verification |
| PSM diagnostics | Actual ON/OFF modules compiled in965, independent hashes match | Diagnostic device capture; event counts are not hardware retry rates |
| Main/Guest, HWNAT, settings/access | Configuration/image checks and scoped source guards | Integrated physical continuity, offload/isolation and persistent settings tests |
| WebUI | Dedicated candidate controls/IPC components exist | Activation binding and complete backend/form integration before release exposure |

## Evidence

- [965 target modules](evidence/WR1200JS-IOT-OPTIONAL965-TARGET-2026-11-09.json): baseline/reload/WSC ELF32 MIPS and CLOSE object independently checked. Source232c4a6, not current HEAD; production_installed=false.
- [RC client ABI](evidence/WR1200JS-IOT-RC-ABI-B8CD491-2026-11-09.json): actual b8cd491 MIPS client object and readback relocation. Not full RC link.
- [PSM variants](evidence/WR1200JS-IOT-OPTIONAL965-PSM-2026-11-09.json): independent module hashes; no physical PSM result.
- [Reopen contract](WR1200JS-IOT-REOPEN-EVIDENCE-GAP.md), [queue controls](evidence/WR1200JS-IOT-BMC-QUIESCE-BOUNDARY-2026-11-09.json), [SN/format](evidence/WR1200JS-IOT-TXS-SN-FORMAT-RECHECK-2026-11-09.json).

## Next gates

1. Finish current CI: optional966 sourceb8cd491; standard967843f and9681c; ABI7495a3. Inspect exact source/input artifacts, not run-head alone for optional overrides. Queue required optional after each eligible standard succeeds.
2. Keep missing RF/TxS contract separate from MCU ACK reuse. Do not bind QUIESCE to admin DOWN, empty bridge/NVRAM, reference CLOSE or unconfirmed queue writes.
3. Complete strong activation/service/shutdown integration only with its required driver ownership and quiescence evidence. No weak or constant-success fallback.
4. After IoT software requirements pass, continue Modern WebUI/Zapret2 and final image/release verification. Device actions require separate owner authorization.

No firmware/module ZIP was retained locally for this audit; archive/artifact
inspection used memory. Preserve source, compact evidence and unfinished work.
