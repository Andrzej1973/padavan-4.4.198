# WR1200JS initial-origin physical lifecycle candidate

The pre-created ra2 may remain never opened after boot. Its idle observation
is not an OPEN token or released CLOSE receipt. WPIQ/WPIR represent that origin
separately from existing WPSQ/WPSR, sharing only Linux CLOSED_CONFIG ioctl0x89fd.
No firmware protocol, MCU ACK reuse, shared DMA queue or radio timing changes.

`prepare-physical-initial-storage.py --bind-main --install-endpoint` extends the
isolated no-host deferred candidate only. It stages adapter metadata/free guards,
Main-worker binding, ARM admission/publication, read-only QUERY, checked Main
completion, persistent CANCEL/RELEASE cleanup and privileged ioctl dispatch.
The optional peer82 pipeline compiles this resulting candidate and pairs the
module with existing RC/httpd candidates for image verification. Its execution
at this revision is pending; this document does not claim target compilation.

ARM retains the exact current never-opened idle observation and Main lifetime,
then acquires native extra task/module/netdev references. Main-worker validates
that origin before RUNNING. QUERY does not submit DOWN; COMPLETE is published
only from existing Main release, native-reference, table and shutdown receipts.
CANCEL is allowed before Main-close admission; RELEASE requires checked COMPLETE.
Partial cleanup remains retained. Lost replies use exact caller/nonce/attempt
identity, without repeating native puts or reacquiring ARM references.

A completed CANCEL may be replaced by a fresh-nonce ARM only by its retained
PID owner with the same current Main/initial ra2 history. Failed admission
restores the previous CANCEL record/cache. Successful admission retires its
PID reference outside locks and preserves monotonic attempt numbering.
A completed RELEASE cannot use this cancellation-only shortcut.

Verification:

- Full host physical-stop suite exited0 with all1803 tool inputs unchanged.
  This baseline predates the final CANCEL replacement change. Exact inputs,
  output and result: evidence/WR1200JS-INITIAL-FULL-HOST-{INPUTS-,}2026-11-15.*.
- After applying replacement, rearm, provider, ioctl, deferred staging and
  storage staging checks all passed. C fixtures use ASan/UBSan and injected
  kernel primitives. Exact results/hashes:
  ../evidence/WR1200JS-INITIAL-CANCEL-REARM-APPLIED-2026-11-15.json.
- Candidate manifests and source transforms are SDK-fragment preparation
  evidence; physical-stage inputs in host fixtures are injected actors.

Remaining before activation:

1. Complete actual pinned SDK/MIPS build and inspect candidate image/components.
2. Add the distinct initial client/session and fresh initial-origin selection
   to RC physical OFF; carry tagged RELEASE through OFF/reopen/shutdown consumers.
   See ../evidence/WR1200JS-INITIAL-RC-INTEGRATION-AUDIT-2026-11-15.json.
3. Keep production normal-shutdown routing unarmed until its complete ownership
   chain is verified. Device tests need separate owner permission.
4. Verify ordinary Main/Guest/IoT behavior and physical OFF/reopen on WR1200JS.

Software candidate preparation, target build, final image inspection and device
acceptance remain separate evidence levels. IoT and the port remain incomplete.
