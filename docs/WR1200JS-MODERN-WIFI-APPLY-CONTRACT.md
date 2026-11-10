# Modern Wi-Fi integration contract — 2026-11-10

Owner requires complete Modern pages, including settings, subpages and dialogs.
The image-verified read-only shell and Classic links are intermediate evidence.
Sol remains the sole writer; source development does not authorize router changes.

## Verified existing path

Pinned source: `c25283e915a2a00a763774dd255b14aff997285e`.

| Surface | Actual request / implementation |
|---|---|
| Main 2.4 GHz | `Advanced_Wireless2g_Content.asp:267`, POST `/start_apply.htm`, hidden iframe; `sid_list=WLANConfig11b;` at line 272 |
| Main 5 GHz | `Advanced_Wireless_Content.asp:278`, same route; `sid_list=WLANConfig11a;` at line 283 |
| Request metadata | `current_page`, `next_page`, `action_mode`, `action_script`; values set by existing page validation/apply logic |
| Persistence | `web_ex.c:update_variables_ex` (base line 1170), existing service-table/validate/apply loops |
| Shared preflight | `tools/prepare-shared-wifi.py` inserts `wr_shared_wifi_prepare` before any service loop; no independent Modern persistence store |
| Planning | `tools/shared-wifi/plan.h:wr_shared_wifi_make_plan`, `adapter.h:wr_shared_wifi_prepare/wr_shared_wifi_value` |
| 2.4 GHz restart metadata | base `variables.c:1237 rt_ssid`, `1256 rt_wpa_psk`: `EVM_RESTART_WIFI2` |
| 5 GHz restart metadata | base `variables.c:822 wl_ssid`, `835 wl_wpa_psk`: `EVM_RESTART_WIFI5` |

These references describe source behavior, not safe physical restart acceptance.
MCU/TxS/RF IoT blockers remain separate and unchanged.

## Existing invariants to preserve

- Shared enable requires all six coherent SSID/security/PSK fields, an explicit
  source band and both exact service memberships. Do not borrow missing fields
  from NVRAM implicitly: the existing adapter deliberately rejects that case.
- Shared disable snapshots both bands and preserves their current credentials;
  forged submitted credentials cannot replace that snapshot.
- Advanced-only changes preserve the shared selector and do not synchronize
  credentials. Channels, widths, schedules and guest settings stay independent.
- Invalid shared requests stop before persistence; arbitrary scripts and
  unsupported action modes cannot bypass coordinated validation.
- Preserve encoded SSID generation in the existing apply implementation.

## Next implementation slice

1. Define an authenticated public configuration projection (stored values, not
   a claim of live association). Exclude PSKs and other secrets from dashboard
   JSON. Distinguish unsupported security modes from empty settings.
2. Design explicit retain/change password intent. Blank input must never mean
   erase or silently reuse a key. Any server-side retention extension must be
   explicit, scoped, validated before writes and tested for both bands, shared
   sync, shared disable and conflicting/forged fields. Preserve rejection of
   ordinary incomplete Classic requests.
3. Build Modern forms with existing NVRAM names and backend apply path. Add
   validation, review/confirmation, credential clearing, failure/reconnect
   feedback and keyboard/mobile handling. Keep all currently supported Classic
   modes in scope; a WPA-Personal subset cannot count as the completed page.
4. Test rejected requests perform no writes; unchanged secrets and unrelated
   band/guest/advanced values remain unchanged. Test actual generated HTTP
   preflight as well as pure planners. Then require target/image checks and
   separately authorized physical acceptance.

No new write endpoint, secret-retention behavior or working Modern apply form
is implemented by this contract. Do not expose an Apply button before its full
request and response path is verified.

## Checks performed now

Strict host GCC + ASan/UBSan passed existing `check-validate.c`, `check-plan.c`
and `check-adapter.c`: UTF-8/byte bounds, both source bands, malformed/conflicting
requests, explicit disable snapshots, advanced-only preservation and unchanged
output on rejection. Binaries/cache are disposable and were removed. This is
host evidence only; optional978 targets the existing exact `7a7d620` package.

## Explicit password-intent prototype — source/host stage

`tools/webui-preview/password-intent.h` implements a pure WPA-Personal planner.
Only `keep` and `change`, with exact `rt`/`wl` band, are accepted. `keep` must omit
the posted PSK entirely and reads only that band's stored PSK through a supplied
read callback, after public-field validation. `change` validates the posted key
without reading the old one. Success owns a bounded snapshot; rejection leaves
output unchanged. A volatile clear function wipes owned temporary plans.

`check-password-intent.c`, run by `check_json.py`, covers exact secret selection,
changed source after snapshot, missing/invalid/contradictory intent, invalid public
fields, stored/new invalid PSKs, raw hex and cleanup. It passes strict host GCC
and ASan/UBSan. No production adapter/header installation or NVRAM persistence
is added at this stage. Full CGI integration must still verify lifetime/cleanup
on all exits, whole-request rejection before writes, shared sync/disable and
legacy Classic behavior. This helper alone does not enable Apply.

## Credential-request guard prototype — not a persistence gate yet

`password-request.h` reads explicit version/band/intent CGI fields, requires the
expected shared selector to match stored state and rejects shared-selector/source
changes through the band request. It enforces the exact Apply mode, empty script
and exact WLAN service set, and rejects posted common credential fields for the
opposite band before retrieving any stored secret. The existing validator and
owned password snapshot remain authoritative for the credential subsection.

`check-password-request.c` verifies rejection without secret retrieval/output
mutation for malformed metadata, stale shared selector, service spoofing,
other-band credential injection and contradictory keep intent. Strict host GCC
and ASan/UBSan pass; it runs in `check_json.py`.

This is not yet wired to the actual HTTP service loop. It does not validate
all radio/guest fields, ensure whole-configuration freshness, solve shared-copy
persistence ordering or authorize an Apply button. Final integration must apply
the existing shared planner and a complete persistence field filter, preserve
legacy Classic semantics and clean the snapshot on every exit. The shared-state
comparison detects a changed selector only; it is not a full configuration epoch.

## Actual CGI binding candidate — isolated, not deployed

`prepare-password-candidate.py` patches an already shared-Wi-Fi-prepared source
copy. It installs the candidate headers, creates a request-owned key context,
runs explicit Modern credential admission before the existing shared preflight,
and provides the owned snapshot to that preflight's CGI read callback. With no
Modern marker, ordinary Classic reads remain unchanged. Every explicit return
from `update_variables_ex` clears the owned key. Existing service dispatch is retained. The isolated candidate now filters its
actual persistence lookup after shared-plan value projection, as described below.

`check_password_candidate.py PINNED_ARCHIVE` extracts three required source files,
runs the actual shared and candidate generators and compiles the actual generated
preflight prefix/callbacks under strict host GCC and ASan/UBSan. It verifies
explicit keep enters shared planning, ordinary missing PSK remains rejected,
script rejection precedes secret read and change uses only the submitted key.
It statically checks cleanup at each return; it does not execute the complete
service loop or prove persistence/notification ordering. Scratch is removed.

Neither script is invoked by the production installer or firmware workflow.
Required before deployment: complete persistence field filtering (including
opposite-band radio/guest values), radio/regulatory validation, shared-copy/
disable behavior, all cleanup/error paths, full HTTP response/reconnect contract,
feature/target builds and separately authorized device acceptance. Do not enable
Apply merely because this credential binding candidate passes host checks.

## Credential-only persistence filter — isolated candidate

The candidate adds a request context parameter to the actual
`validate_asp_apply` function and all three existing service-loop call sites.
Immediately after `wr_shared_wifi_value`, it admits only the six main-network
credential fields for the selected band. Opposite-band credential values pass
only when the existing shared planner produced `WR_SHARED_SYNC`. The shared
selector value remains the planner's preserved value; caller selector mutation
is rejected by credential admission. Direct encoded `ssid2`, own/opposite radio
fields, guest fields and unrelated names return NULL and cannot enter the normal
value-write branch. Without a Modern marker the filter is a passthrough.

Actual generated helper execution verifies exact-name matching, guest/radio/
encoded/prefix-injection rejection, shared credential propagation and legacy
passthrough. Source checks verify filter order and all three call bindings.
The existing code has a similar lookup in legacy `validate_cgi`; the generator
therefore scopes its patch to `validate_asp_apply` and refuses ambiguous anchors
before mutation. Strict host GCC + ASan/UBSan pass.

This deliberately admits credentials only at the current candidate stage.
Radio controls remain disabled; their complete regulatory/channel/width admission
and fields must be implemented before full-page acceptance. The actual complete
HTTP persistence loop/firmware binary still needs execution/target verification;
this is stronger than a pure planner test but not complete CGI acceptance.

## Radio admission source investigation — 2026-11-10

Pinned `user/rc/ralink.c:492` maps country codes through `ralink_cc_table` into
CountryRegion. MT7603 `common/cmm_sync.c:67` selects descriptors from
`common/rt_channel.c:75-159`. The Classic `wireless_2g.js:493` computes its own
browser options and includes a Debug/channel14 case; this is not an authoritative
server-side admission result. The extracted country/driver mappings and source
hashes are recorded in `docs/evidence/WR1200JS-MODERN-RADIO24-POLICY-2026-11-10.json`.

Important: MT7603 `os/linux/ap_ioctl.c:301-329` handles `SIOCGIWRANGE` by zeroing
`iw_range` and setting version/quality fields; it does not fill channel/frequency
lists. Although httpd `ralink.c:1432` calls it, it cannot supply a trusted list of
active channels for Modern admission. No new scan or device query was performed.

RC fallback for an unknown country and an inherited browser list cannot authorize
radio writes. Effective driver/EEPROM/SKU restrictions must be reconciled or read
through an existing supported driver path. Debug/channel14 remain excluded from
Modern. Source descriptors alone are not hardware/runtime acceptance. The
candidate continues to block all radio persistence until this is resolved.

Read-only page02 dependency corrected to match Classic: HT width/extension are
hidden for b-only, b/g and g-only modes. A regression case executes that renderer;
unknown modes also do not expose HT assumptions. This changes presentation only.

## Existing channel-query candidates and pure radio guard

Full vendor source scan finds `OID_802_11_GET_CH_LIST` only as a definition in
`include/oid.h:1174`, not a matching handler. `Set_ChannelListShow_Proc` in
`common/cmm_info.c:1372` is conditional on EXT_BUILD_CHANNEL_LIST, prints to the
kernel log and can assign `CommonCfg.DfsType` at lines1398-1399. It is not a
proven read-only active-list API. Text writer inventory is recorded separately;
its lexical matches include comparisons and indirect arrays and are leads, not
an exhaustive semantic synchronization proof.

`radio24-validate.h` validates a request against a supplied trusted server policy.
It rejects unavailable/unverified/empty policies and masks containing channel14,
checks canonical channel strings, booleans and PHY modes, ensures the primary and
selected secondary channel are within the mask, and requires inapplicable HT
fields to be omitted. Auto-channel mode remains subject to the driver's own
selection/coexistence behavior. This pure guard does not scan, modify NVRAM or
invent channel permissions. The policy mask must never be accepted from CGI.

Strict host GCC/ASan/UBSan fixture covers region-like masks, unavailable policy,
channel14, malformed/unsupported values, secondary bounds and legacy omission.
No effective-policy provider is bound; no radio persistence or Apply is enabled.
Source RC tables alone must not set the provider's verified flag without
reconciling effective EEPROM/SKU/driver restrictions. Next investigate a bounded,
synchronized driver snapshot or another source-proven existing API.

## Complete apply-validator execution — host fixture

`check_password_candidate.py` now extracts and executes the entire actual
candidate `validate_asp_apply` function, in addition to its generated preflight.
`persistence-fixture.c.inc` supplies representative service tables and in-memory
NVRAM; hardware/network/file helpers abort if unexpectedly reached. The actual
value loop, shared projection, Modern filter, comparisons, NVRAM write calls and
event-bit accumulation execute under strict GCC and ASan/UBSan.

Four scenarios pass: independent keep/change and shared keep/change. Assertions
check selected/other band SSID and key results, unchanged radio/guest values,
blocked injected script-file and encoded-SSID fields, preserved auth settings,
expected restart bits and replay without extra writes. The SSID encoder is a
fixture substitute: this verifies delegation, not percent-encoding correctness.
The tables are representative, not the full target variable tables.

This proves more than a pure planner or prefix test, but not the entire HTTP
server/service dispatcher, actual NVRAM persistence, target binary, notification
execution or device behavior. Source still isolated; radio admission/provider,
HTTP response, complete lifecycle cleanup and target feature checks remain open.

## Commit, notification and browser-response boundary

Pinned `start_apply.htm` evaluates `update_variables`, `asus_nvram_commit`, then
`notify_services`. Its JavaScript callbacks and timed redirects are designed for
Classic parent pages; Modern cannot treat the timer or HTTP200 as radio success.
Modern must report explicit rejection, saved-state observation, storage policy,
notification request and unconfirmed reconnection separately.

Actual `nvram_commit_safe` honors `nvram_manual=1`, skipping automatic flash
commit. Actual `asus_nvram_commit` resets its dirty flag, and `ej_notify_services`
clears pending event/per-band flags after requesting RC actions. An RC request
is not proof of a completed restart or working Wi-Fi.

The host persistence fixture now executes these three actual callbacks after
actual writes in eight combinations (independent/shared, keep/change,
automatic/manual). Flash/RC calls are counters; reboot or unexpected I/O aborts.
It verifies one automatic commit, none in manual mode, exact band notifications,
cleared flags and no duplicate callbacks. Callback bodies are unmodified;
unused framework parameter warnings alone are suppressed around extracted EJ
callbacks. HTTP transport, actual flash writes/RC completion and device behavior
remain unverified. Evidence: WR1200JS-MODERN-APPLY-LIFECYCLE-HOST-2026-11-10.json.

## Alternate legacy entry guard

The isolated candidate now rejects a present `wr_modern_wifi_version` at the
start of legacy `validate_cgi`, before variable iteration. Only coordinated
`update_variables_ex` may admit that marker. This prevents interpreting a Modern
credential request under ordinary legacy persistence semantics. The actual
extracted guard is executed with marked/unmarked fixtures; ordinary Classic
requests without this marker retain the existing path. This is still source/host
candidate evidence, not production HTTP transport acceptance.
