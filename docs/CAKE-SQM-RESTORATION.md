# WR1200JS CAKE/SQM — included, factory OFF

Owner clarification2026-11-11 supersedes older "without CAKE" goal/scope text.
Include the backported kernel module, compatible tc/SQM lifecycle and existing
Classic control. Factory `sqm_enable=0`; no automatic CAKE activation or new
load-based mode is introduced. Preserve saved settings and acceleration
preferences. IoT on Ubuntu22.04 remains the primary development workstream.

## Cause of the mismatch

Commit2be79601 (2026-10-11) recorded `CONFIG_FIRMWARE_INCLUDE_SQM=n` and an
explicit exclusion comment. Later firmware CI enforced requested/effective
exclusion and absence of sch_cake.ko. Therefore image1024's reported absence
was real and consistent with that older policy, not a compiler-cache failure
or a module randomly lost during compilation. Older image evidence remains
historically valid, but an image without CAKE does not meet the corrected scope.
The app's recurring goal text may still carry the obsolete phrase; this owner
clarification is authoritative. No unsupported goal-database edit was performed.

## Existing implementation path

- Pinned vendor `trunk/configure` SQM section selects CAKE as a module;
  `prepare-packaging.py` keeps IFB modular.
- Classic `Advanced_SQM.asp` submits `SqmConf` and sqm_enable/rates through the
  existing HTTP variables table and EVM_RESTART_SQM event. APP_SQM exposes the
  existing capability and controls. No Modern page development is resumed.
- Factory `trunk/user/shared/defaults.c` sets sqm_enable0. Prepared RC
  start_sqm_locked refuses anything other than explicit enable1, AP mode,
  existing activity or absent WAN. Existing serialized lifecycle inhibits
  acceleration temporarily only for shaping and does not commit altered
  persistent HWNAT/SFE preferences. Physical transitions remain unverified.
- Installed `/usr/lib/sqm/run.sh` validates rates/interfaces and creates owned
  queues only through explicit start. CAKE/IFB/ingress helpers remain modules.

## Changes and checks

Requested SQM inclusion is now y. Existing final gates verify CAKE vermagic,
MIPS tc and its CAKE parser, script/page/locales and compiled RC integration.
A WR1200JS CAKE capability manifest is runtime-unverified. Additional gate checks
effective required kernel components, installed modules/script/control and
factory OFF; it rejects CAKE as the default kernel qdisc. Historical exact-source
verification can still inspect old excluded profiles without redefining them.

Native tests passed against the actual prepared pinned RC helper: default OFF
has no start/inhibition calls, while explicit-enable and AP/running/WAN/failure
paths retain their behavior. OS operations are injected. Real Make packaging
fixtures and config/image-policy counterexamples pass. These are host/source
checks, not target build, final-image inclusion or runtime acceptance.

Next: GitHub Ubuntu22 standard for this source, inspect actual CAKE module/tc/
ROMFS and final TRX size, then required optional IoT on its exact SHA. Do not
activate CAKE, flash or change router settings without separate direct approval.
The staged repository-audit draft was updated to the real SQM selector; its
unrelated unpublished architecture work remains outside this package.
