# WR1200JS IoT verification checkpoint — 2026-11-18

Published branch: `codex/wr1200js-service-webui`.
Published revision: `13ce5dffcd952b8118ace48bc5a1c5ee7e0aa25f`.

- Standard1376 / 44167754040: success, including firmware build and ZIP jobs.
- ABI930 / 44167774435: success for the same revision.
- Optional1377 / 44229421135: dispatched for that exact revision after checking
  standard success and existing runs. Ubuntu24.04, source toolchain, WR1200JS,
  IoT peer82, candidate checks enabled. Last observation: in progress at
  `Check IoT host compiler compatibility early`; no target/image result yet.
- Optional1373 / 44165025483, older revision
  `87f2ed5ab8555bedc177d37b4e6d2d9a211a96f2`: independently audited merged
  candidate artifact14365119640. Exact pair recomputed with that revision's
  package verifier; image SHA256, header/payload CRC, embedded MIPS replacements,
  module vermagic and actual-path RC/HTTP dependency closure passed.
  See `WR1200JS-OPTIONAL1373-INDEPENDENT-IMAGE-2026-11-18.json`.
  This does not cover the later edit/view or Classic candidate package.
- Terminal audit extraction and archive removed; 198205440 allocated bytes
  reclaimed, with the small audit and cleanup reports retained.
- Current local edit/view focused suite completed with exit0 using the pinned
  native Linux source and native HTTP preparation fixture. Includes early RC
  header closure, private view/lease/queue composition, Save ownership, strict
  C/ASan/UBSan checks and simulated Classic DOM tests. Classic ROMFS staging
  fixture also passed separately. These are host/source checks.

Local Classic script hardening remains unpublished: bounded view fields and
110-second browser expiry/clock-regression refusal. The RC's existing monotonic
lease validation remains authoritative. These local edits are not covered by
the running optional1377.

No router operation, physical acceptance, main-image promotion or ACK safety
completion is claimed. Keep unrelated shared-checkout changes intact. Next:
inspect optional1377's actual result, triage any first actionable failure using
the failure monitor and original log, then independently inspect its candidate
TRX and Classic assets. Continue mandatory IoT implementation beyond these
checks; four final release variants and device acceptance remain outstanding.
