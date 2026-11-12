# WR1200JS IoT acceptance ledger — 2026-11-11

IoT is mandatory for the release. The current image is a development checkpoint,
not an IoT release. Ubuntu24.04 is the default CI host after optional1028
verification. The existing local WSL installation also runs Ubuntu24.04.5.
Ubuntu22.04 remains an explicit CI control. Modern WebUI development remains paused.
This ledger distinguishes implementation from acceptance and supersedes older
"currently running" snapshots only for the checkpoints explicitly listed here.

| Required behavior | Authoritative evidence inspected | Remaining acceptance |
| --- | --- | --- |
| Reserve third2.4GHz BSS; default OFF, independent credentials | Prepared peer82 source/profile checks; source guards compiled in isolated MT7603 module | Actual cold-profile/RC/controller binding and final-image inclusion; secure defaults and reboot on device |
| Toggle ra2 without physical restart/scan, preserving Main/Guest | Composed owner/admission tests and isolated driver build | Complete production call chain and Main/Guest associations on device |
| Bind OPEN to current loaded profile/key, epoch and owner | Linux driver API/client and bounded publication/readback host/target evidence | Production transaction binding; host publication is not RF delivery |
| Preserve sleeping-ra2 queued traffic and TIM indication | Optional1018 actual prepared-source21-case PSM check and five target modules; generated helper hash verified | Loaded target behavior with sleeping/waking clients, queue limits, idle expiry and concurrent Main/Guest traffic |
| Safe OFF, failure recovery and reopen | Checked CLOSE/reference accounting and recovery/join implementation compiled in candidate | Proven per-BSS RF/DMA/late-TxS boundary before release/reuse; configuration CLOSED, stage4 or zero outstanding snapshot is insufficient |
| Firmware ACK safety through restart/scan | Stale-ACK and sequence protections remain in place | ROM delivery/correlation or another proven safe lifetime boundary; restart/scan exhaustion is not fixed by the PSM policy |
| Safe PCI/DMA/IRQ/work teardown | Isolated source guards and target-feature compilation | Complete physical lifetime/quiescence evidence; no inferred receipt from reference counts alone |
| Isolated subnet, owned bridge, DHCP/DNS, internet, LAN/router firewall | Staged network/controller operations; archived native namespace packet and DHCP/DNS evidence | RC/driver transaction binding, final image and actual client tests |
| Correct IPv6 policy | Staged IoT bridge disables IPv6 and filters closed | Production image enforcement and device check; IPv6 internet service is not implemented/claimed |
| Configuration persistence and recovery | Request snapshots and staged ownership/recovery models | Production save/apply/reboot/failure-recovery acceptance |
| Main/Guest, HNAT and physical port preservation | Image HNAT excludes ra2/br-iot and preserves Main paths; config/image gates | Device traffic/isolation/offload tests |
| Mandatory firmware inclusion and complete management UI | Implementation contract; preserved UI/settings sources | IoT is not installed in the current production path; UI remains paused, not complete |

## Exact checkpoints

- Standard1016/43053592915 (Ubuntu22) and1017/43053615585 (Ubuntu24),
  source4f80200: successful workflows, independently checked actual TRX CRC,
  size, MIPS/product identity and embedded HNAT policy. Full effective configs
  and SquashFS path inventory compared. These do not establish IoT installation.
- Optional1018/43058250743, Ubuntu22, source4f80200, artifact13873798948:
  baseline MIPS module5910000B SHA256
  dc8c0d4abf84ac7a5138dc2bcf05176ea9c5cae8b9ec58c870d6ab8b69f7f04e;
  PSM ON/OFF, reload and WSC module bytes/hashes independently verified.
  Final reports explicitly retain production_installed=false/runtime_verified=false.
- Standard1020/43061810202 and1021/43061833084 at60072c1 succeeded.
  Optional1022/43065263578 Ubuntu22 succeeded; its current actual artifacts
  still need inspection before promoting it to an independently verified checkpoint.
- Optional1023/43065290017 Ubuntu24 failed a generated WDS host fixture warning,
  not firmware ACK or a cache error.08294cd initializes opaque fixture tags and
  adds broader early preflight. Standard1024/43069654850 Ubuntu22 succeeded.
- Standard1025 Ubuntu24 and optional1026/43073222448 Ubuntu22 succeeded
  for08294cd. Optional1028/43076227476 Ubuntu24 also succeeded for that exact
  source. Actual artifact13884390903 contains five MIPS modules whose hashes
  match the final baseline/PSM/reload/WSC reports. This checkpoint remains an
  isolated candidate with production_installed=false/runtime_verified=false.
- Standard1029/43080683236 source82044a failed during guide generation after
  successful CAKE inclusion/default-OFF/manual-control image gates. Source
  0e36777 adds the SQM guide and precompile coverage. Standard1030/43085305425
  succeeded. Actual TRX13122651B SHA256
  4a28d8ed4f2255f66c4d5b2aca77c804a4a53c4e130aa2ae0af72c6da4899ccb
  passed independent CRC/DTB/SquashFS and five CAKE MIPS-module checks.
  Optional1031/43087507884 succeeded for the exact0e36777 source. Actual
  artifact13887468464 five MIPS modules match their final size/hash reports.
  PSM ON/OFF object hashes and compile flags, feature report linkage and
  vermagic4.4.198 independently checked. Production and runtime remain open.
- Local Ubuntu24 GCC13.3 passed58 existing standalone ASan/UBSan IoT fixtures,
  actual CLOSE composition and WDS producer capture after the OS upgrade.
  Injected host behavior leaves the RF/DMA/late-TxS boundary unverified.

Evidence: ../evidence/WR1200JS-IOT-OPTIONAL1018-TARGET-2026-11-11.json,
../evidence/WR1200JS-UBUNTU-STANDARD1016-1017-2026-11-11.json,
../evidence/WR1200JS-UBUNTU-STANDARD-CONTENT-2026-11-11.json,
../evidence/WR1200JS-IOT-OPTIONAL1023-HOST-FIX-2026-11-11.json,
../evidence/WR1200JS-UBUNTU24-OPTIONAL1028-2026-11-11.json,
../evidence/WR1200JS-BUILD1029-GUIDE-FAILURE-2026-11-11.json.

## LE telemetry target checkpoint — 2026-11-12

Standard1033/43136969650 succeeded for89def54; actual TRX independently
passed CRC/size/product/MIPS/HNAT checks. Optional1034/43147103108 succeeded
for that exact source. Actual artifact13912579138 five MIPS modules match
final reports. New LE/TIM marker is present in PSM ON module and txs.o,
absent in OFF module and txs.o; object/command hashes and flags verified.
Evidence WR1200JS-IMAGE1033-2026-11-12.json and
WR1200JS-IOT-OPTIONAL1034-TARGET-2026-11-12.json. Production binding,
per-BSS safe OFF/reopen and physical runtime remain open.

## Next gates

1. Standard1030 image and optional1031 target artifacts for0e36777 are
   independently verified. Evidence is WR1200JS-IMAGE1030-2026-11-11.json
   and WR1200JS-IOT-OPTIONAL1031-TARGET-2026-11-11.json. Further equivalent
   builds do not establish the missing lifecycle contract.
2. For safe OFF, obtain or establish a supported per-BSS flush/retirement receipt,
   a command/report correlation contract, or a proven lifetime/pacing design that
   handles late reports across reopen. Do not assume delay, host generation,
   DMA_DONE, idle bookkeeping or larger ID pools supply that proof.
3. Complete RC/controller/driver binding without substituting constant-success
   shutdown stubs or removing isolation on an uncertain result. Verify mandatory
   image inclusion and configuration before any production acceptance claim.
4. Device-side tests/flash/reboot/service/configuration changes require the owner's
   separate direct permission. They have not been authorized by this ledger.
