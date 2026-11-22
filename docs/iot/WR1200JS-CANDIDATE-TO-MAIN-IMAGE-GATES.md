# WR1200JS IoT candidate to main-image gates

This is a historical evidence map. Revision-specific observations and proposed
next steps below do not establish current main-image readiness. Check the
current status/handoff and exact source before using them as an active plan.

Reviewed source:859b9769, 2026-11-16. This is an evidence map, not promotion.

## Existing chain

1. `compile-runtime-link.sh` copies the SDK RC/HTTP/IAPP trees into an isolated
   probe. It runs `prepare-rc/http/control/runtime.py`, IAPP policy preparation
   and `check-runtime-source.py`, then restart entry preparation and its manifest
   verifier. These checks compare actual generated source/header bytes and hook
   order; they do not merely trust the pair JSON.
2. The target SDK links RC/HTTP. Object symbol checks require INITIAL entry,
   selection, INITIAL/cold normal-shutdown readiness/commit and private cold-root
   handoff functions. Binary inspection
   rejects undefined IoT symbols; the dependency checker binds actual binary
   hashes to available ROMFS libraries. Original binaries/configs are hashed and
   checked unchanged.
3. `package-candidate-pair.py` binds those binary hashes, driver module, kernel
   config and generated manifests. Since ace688d9 it refuses missing/untyped
   runtime/restart lifecycle evidence. Its marker means manifest-contract proof,
   not firmware execution or RF completion.
4. `ci-stage-candidate-romfs.sh` requires the same kernel configuration, stages
   exactly RC/HTTP/IAPP/module replacements, preserves unrelated entries and
   checks dependencies at real image paths. It builds an isolated TRX and checks
   its board gates, CRCs and complete ROMFS comparison in CI.
5. Optional1342 source502d497e has independently checked TRX, selected MIPS
   replacements/DSO closure and lifecycle-pair evidence. It excludes859b9769
   cold arm/handoff integration. Standard1343 and ABI909 verify859b; optional
   target/image verification is required after standard succeeds.

## Required before any main-image promotion

- Exact latest-source standard, ABI/host suite and optional target/feature/full
  RC/HTTP link success, with dispatch and verified revision distinguished.
- Independent actual candidate TRX/embedded binaries/module verification for
  that source, including the new shutdown symbols and manifest contract.
- Review production install/call-chain changes against saved settings, Classic
  controls, Main/Guest, HNAT, port layout, default-OFF IoT and IPv6 fail-closed
  policy. Existing isolated packaging is not evidence of main-image installation.
- Explicit image/configuration/release checks for the resulting main image.
  Keep MCU stale-ACK protection, DMA ownership and radio timings unchanged.
- Device acceptance remains separate and requires the owner's direct permission:
  no flash, restart, service or configuration changes are authorized here.

Do not flip `production_ready`/`production_installed` or rename the isolated
candidate as a completed release to close these gates. Continue actual source
integration and its checks; physical runtime remains unverified until tested.

## Blocking source integration work before Classic Apply

Authenticated wr_iot_apply.cgi queues a runtime request. request-stage.c writes
only _t keys; start-commit.c commits DNS and suspends the runtime snapshot. The
nine-key rollback snapshot likewise covers only _t values. Saved cold profile
wr_iot_enable/ssid/psk is read separately, and factory CSPRNG reservation cannot
be used as configured runtime ON. Thus applied runtime state is not saved
configuration or reboot persistence. Classic navigation currently has only a
pending page. Standard firmware explicitly excludes the wr-iot RC directory.

Next trace the native SDK configuration/flash-save API, then implement saved
configuration under the existing RC operation owner. A direct HTTP NVRAM writer
would bypass that owner. Credential changes must preserve the existing loaded
profile proof and must not alter saved identity while a current backend still
needs it for safe OFF. Provisioning/explicit configuration restart and ordinary
virtual IoT ON/OFF require distinct behavior. Ordinary toggles must keep Main/
Guest connected and must never restart/scan physical Wi-Fi.

Require atomic/recoverable save ownership, setter/readback failure retention,
reboot/default-OFF behavior and honest Classic queued/applied/saved/unknown
states before enabling the page. Reuse native save behavior and keep IoT
controls in Classic. The 2026-11-22 owner decision selects Classic as the sole
firmware WebUI and supersedes the earlier Hybrid Modern resumption. IoT remains
first priority. This does not establish target/image/device acceptance. Source evidence: ../evidence/
WR1200JS-IOT-CLASSIC-PERSISTENCE-GAPS-2026-11-16.json.

## Native configuration API inspection — 2026-11-17

Pinned SDK c25283e provides per-key NVRAM SET and COMMIT ioctls. SET uses the
kernel spinlock per tuple; COMMIT snapshots non-temp values under that lock
before separately taking the flash mutex. These do not establish a multi-key
Apply transaction. The native HTTP nvram_commit_safe skips manual mode1 and
otherwise discards the commit result. Stock file_lock blocks on F_SETLKW and
cannot simply become a nonblocking PID1 owner.

Preserve existing save behavior and separate applied runtime from saved or
manual-save-pending status. Avoid adding an asynchronous flash writer. Next
implement and compose owned requested/saved configuration before connecting
Classic Apply. Include factory provisioning, legacy settings preservation,
partial setter/readback failure and loaded-profile identity across OFF/restart.
Evidence: ../evidence/WR1200JS-NATIVE-CONFIG-API-2026-11-17.json.

Standard1343, ABI909 and optional1344/44009604392 succeeded for859b9769.
Independent image audit is recorded in
../evidence/WR1200JS-OPTIONAL1344-INDEPENDENT-IMAGE-2026-11-17.json.
That image predates the mailbox ACTIVE auto-arm change and does not validate it.

Persistence must not serialize an ordinary OFF request over a saved profile:
request.h deliberately returns enabled0 with empty credentials/subnet on OFF.
precreated-profile-request.h and its existing test retain validated SSID/key
while default OFF. Keep the saved provisioning record distinct from the runtime
OFF command; do not erase credentials or network settings when toggling OFF.
A saved-profile update also needs complete disabled-profile network validation,
rather than reusing the early-return runtime OFF parser.
