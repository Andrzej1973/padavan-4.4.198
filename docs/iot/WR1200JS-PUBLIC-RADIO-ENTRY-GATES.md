# Public physical radio entry integration gates

Radio ON/OFF owners are process-context APIs. Paired experimental restart
preparation now calls the historical-receipt ON entry before owned restart and
the native fence. OWNED and REFUSED stop fallthrough; NATIVE preserves the prior
path. General OFF/cold routing and production installation remain unbound. The
restart-entry manifest reports this narrow hook independently of the earlier
runtime preparation report.

The stock `restart_wifi_rt(radio_on, need_reload_conf)` hook must distinguish:

| Current provenance | Requested action | Required route |
| --- | --- | --- |
| Historical RC-owned physical OFF receipt | radio ON | new exact request ID/time, guarded saved configuration snapshot, private ON root; enabled0/1 selected from validated saved IoT policy |
| Historical physical OFF receipt | radio OFF | verify still DOWN; never start a second OFF or discard receipt |
| Retained live owned IoT backend | radio OFF | private OFF owner/quiesce, then its complete followup and receipt publication |
| Retained live owned IoT backend | radio ON/reload | existing exact owned restart controller; no native fallthrough after a claimed transaction |
| Initial/never-opened configuration | radio action | native path only after fresh initial-OFF admission; never fabricate a historical RELEASE |
| Any process-owned ON/OFF or uncertain transition | concurrent action | refuse before profile/authentication/radio mutation; preserve existing owner |

Inputs require board/router/AP-mode policy and reload validation. Copy borrowed
NVRAM values under the existing service/config guard; bind a unique transaction
ID and monotonic creation time. Hand over only immutable intent, never copy live
owner structs or keep borrowed service guards across another outer fence.
Return states must distinguish unowned native routing from owned or refused
routing so an uncertainty cannot fall through into combined SDK stop/reopen.

Before binding, reproduce each route with the actual prepared SDK function and
RC controller. Include repeated callbacks, uncertain admission, saved radio/live
radio differences, enabled0/1, reload0/1, initial startup and process-exclusion
windows through WAN/IAPP. Verify source transformation anchors, target C
compilation, RC/HTTPD dependency closure and final installed image separately.
The existing native process-exclusion guard closes a known fallback hole;
it does not itself bind or certify any public route.

Device actions remain subject to separate direct owner authorization. No public
entry or production acceptance is claimed by this document.

Prepared-hook source tests pass all three result routes and existing manifest/
anchor/duplicate protections. Actual saved entry and root composition pass
IoT ON/OFF separately. Target compilation of the paired SDK body and physical
runtime remain separate gates; no router modification occurred.

The paired experimental hook now routes owned physical OFF before saved ON and
owned restart. OFF OWNED/REFUSED cannot fall through; an initial unowned OFF can
reach native admission. Actual entry/RC ppoll/OFF-owner composition verifies
receipt publication once and duplicate refusal with physical/followup actors.
Full cold-path/disabled-root physical OFF handling and target/device gates are
still separate; this hook does not fabricate an owned CLOSE for a never-opened
ra2.

The initial idle API requires Main READY and an owned Main reference. It cannot
certify Main DOWN. `precreated-down-reference.h` now composes the actual completed
Main software-release predicate with strict never-opened ra2 and idle registry
checks. This read-only candidate is not an installed ioctl or physical restart
permission: peer/control/descriptor ownership and pinned lifetime still need
composition. A fresh adapter which never started Main is a separate case.
