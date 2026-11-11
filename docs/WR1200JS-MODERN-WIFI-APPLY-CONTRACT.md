## Work paused by the owner — 2026-11-11

WebUI development and activation are paused until a separate explicit owner
instruction. Current preserved status and resumption steps are indexed in
[WebUI preservation](webui/README.md). Dated implementation notes below retain
their original evidence scope.

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

The persistence checker additionally parses all field names and longname types
from generated `variables_WLANConfig11b/11a` (86/85 rows) and repeats the sixteen
scenarios with injected noncredential values across that entire namespace.
Conditional branches are intentionally unioned; event masks remain fixture
constants. This broadens filtering evidence without claiming exact target-config
or event-table equivalence. Both original representative and namespace-union
fixtures pass strict host GCC and ASan/UBSan.

### Snapshot and HT40 constraints found in actual writers

`BuildChannelList` clears its array before allocating/rebuilding and assigns
`ChannelListNum` at the end; early returns precede count assignment. A snapshot
provider must prove serialization with all writers; equal repeated reads or a
new reader-only lock do not suffice. Direct builder sites are inventoried in
WR1200JS-MODERN-CHANNEL-LIST-CALLERS-2026-11-10.json, not yet a complete lock proof.

The driver computes per-channel `CHANNEL_40M_CAP` using `N_ChannelGroupCheck`.
The pure validator now requires a separate trusted `ht40_primary` mask for
20/40 requests, rejects bits outside the channel mask, fails closed without
capability and rejects an explicitly ineligible primary. A provider must account
for actual flags, secondary pairing and coexistence; the mask is not derived
from browser values or channel presence alone. Host negative cases pass; no
provider is yet bound or radio writes authorized by this guard.

### Existing kernel serialization domain

The pinned Linux `net/wireless/wext-core.c:988-990` holds RTNL around
`wireless_process_ioctl`, including its legacy `ndo_do_ioctl` fallback at958-959.
`net/core/dev_ioctl.c:552-557` similarly wraps private ioctl dispatch. A repeatable
source-anchor verifier records hashes in the CHANNEL-SERIALIZATION evidence.
RTNL is therefore a candidate existing domain, not proof of all driver writers,
adapter lifetime or apply-time policy freshness. Complete the caller audit before
implementing a reader; do not add a lock used only by the new reader.

## Guest schedule read decoder — 2026-11-10

`WifiDemo.guestSchedule` decodes stored Sunday-first seven-character day masks
and independent weekday/weekend HHMMHHMM strings. Invalid shapes or out-of-range
hours/minutes remain unknown; no defaults are substituted. Equal and overnight
intervals remain visible as stored, without claiming valid apply semantics.
`check_guest_schedule.py <pinned-source-archive>` runs the actual Classic
getDateCheck/getTimeRange functions in an isolated Node context and compares all
128 day masks and 1440 start times, plus malformed input cases. PASS locally.
This is a read decoder; Guest JSON projection, accepted page03 renderer,
persistence validation and RC schedule semantics remain unfinished. No router
configuration was read or modified. Existing production renderer tests pass.

## Guest apply classification and RC schedule evidence — 2026-11-10

Pinned `variables.c:1309` maps all Guest fields to EVM_RESTART_WIFI2, but
`web_ex.c:1093` refines enable/date/time/time2 to WIFI_GUEST_CONTROL_BIT;
`ej_notify_services` dispatches control_wifi_guest_rt for that class. Other Guest
SSID/security/isolation/rate fields fall through WIFI_COMMON_CHANGE_BIT and
notify the full Wi-Fi restart. Mixed requests inherit the common restart.
Do not promise Main/IoT continuity for the whole Guest form. Even guest-control
is only a host dispatch distinction: virtual driver open/close needs verification.

Actual `net_wifi.c:1337 timecheck_wifi` executed under ASan/UBSan with clock
and NVRAM fixtures: both bands, every minute of a week, inclusive interval
endpoints, Friday overnight spillover and no selected days pass. Malformed
length returns1 in legacy code; Modern must reject malformed admission rather
than relying on this behavior. Equal-time schedules are rejected by Classic UI
but not fully characterized here; no new apply validator or RC change made.
Evidence: WR1200JS-MODERN-GUEST-APPLY-RC-2026-11-10.json. These are pinned
baseline findings, not prepared-candidate/image/device acceptance.

## Guest schedule admission component — 2026-11-10

`guest-schedule.h` validates exact seven binary day positions and two eight-digit
HHMMHHMM intervals. It rejects missing, malformed, out-of-range and equal-time
intervals; accepts overnight intervals and an empty selected-day set, matching
Classic admission/RC intent. No NVRAM, service, clock or driver access. The
component is not yet connected to CGI or a complete Guest request validator.
`check_json.py` now executes its strict C99 ASan/UBSan fixture:128 day masks,
1440 start minutes, both interval positions, malformed/missing/equal cases PASS.
Do not describe legacy CGI as protected by this unbound component.

## Complete Guest value preflight candidate — 2026-11-10

`guest-request.h` checks band, enable/hidden/isolation/MAC booleans, exact rate
0..9, SSID, supported auth/WPA/crypto, schedule and explicit keep/change intent.
Public validation precedes secret access. Keep rejects any posted PSK (including
empty), reads only selected rt_guest_wpa_psk or wl_guest_wpa_psk, and owns a
65-byte snapshot; change never reads stored key. Open accepts keep-only intent
and preserves dormant stored key without reading it. Plans unchanged on reject
and explicitly wiped by caller. This is a request-value component, not yet CGI
metadata admission, stale-config protection, persistence allowlist, RC execution
or target acceptance. check_json.py runs ASan/UBSan fixture with namespace,
read order, owned snapshot, injected bad public values, rejection and wipe PASS.

## Guest metadata and field-filter candidate — 2026-11-10

`guest-adapter.h` requires exact version/band/Apply/service identifiers, rejects
script/shared-mode/main-Modern markers and opposite-band Guest fields before
secret reads. Calls complete Guest value preflight and binds persistence names
to the owned plan band; only14 exact Guest keys pass, PSK from owned plan only,
open/dormant key suppressed. Actual table-loop and CGI entry integration,
request freshness/concurrency handling and service outcomes remain unfinished.
All other fields are dropped by candidate filter, not written. ASan/UBSan
fixture checks both bands, metadata rejection without secret reads, injected
namespace crossings and exact filter names. No production CGI installed.

Optional983 independently confirms complete earlier credential HTTP candidate
compiles/links for MIPS at fb20d3b. Artifact binary hash/ELF matches report;
production image unchanged. This does not cover new local Guest adapter.

## Isolated actual CGI Guest preparation — 2026-11-10

`prepare-guest-candidate.py` extends the prepared credential candidate in memory
with checked anchors before writing: request-owned Guest plan, preflight before
service table writes, main-field suppression during shared planning, exact
Guest persistence filter, legacy CGI marker refusal and secret cleanup. It is
not called by production installer or target candidate CI yet.
`check_guest_candidate.py` prepares actual pinned web_ex.c and executes its
actual preflight prefix/filter under ASan/UBSan: both bands with stored shared1,
invalid marker/mixed metadata/schedule, no secret on rejection and blocked
Main/radio/IoT/file/shared writes. Full persistence loop, RC notification,
concurrency/freshness, target compile and HTTP response contract remain open.

## Complete Guest apply/commit/notify host fixture — 2026-11-10

Published31e7732:24 scenarios execute complete actual apply/commit/notify code
with substitute NVRAM/flash/framework, both bands/shared flag/manual mode/keep/
change/open. All13 Guest public values and owned-key persistence asserted;
other namespaces preserved, repeated apply/commit/notify idempotent. Repeated
with86/85 actual WLAN names/types union. Existing main credential16 scenarios
pass. Optional compile gate now includes isolated Guest candidate; target result
pending. Not full HTTP dispatcher, actual service loop, concurrency/freshness,
physical isolation or runtime acceptance. Production Guest remains read-only.

## Complete service-loop request sequence — 2026-11-10

Host Guest fixture now executes entire actual generated update_variables_ex,
including service selection, apply branch, response calls, timing and cleanup;
then actual commit/notify.24 scenarios pass twice including86/85 field union.
Pinned start_apply.htm:118-120 calls update_variables, asus_nvram_commit, then
notify_services in one template request. Replaying update before notify resets
restart_needed_bits and loses pending notification: an initially failing fixture
exposed this ordering requirement. Correct whole-request replay after notify
passes without extra writes/commit/notify. Preserve one coordinated request,
never split these three stages across independently retried Modern requests.
Actual HTTP/template dispatch, freshness token and external NVRAM writer races
remain unverified. See Guest REQUEST-SEQUENCE evidence; no production Apply.

## Isolated Guest transport gate candidate — 2026-11-10

Pinned httpd accepts GET/query and POST CGI paths and does not establish Modern
request provenance by marker alone. Added candidate-only guest-transport.h and
prepare-guest-transport.py: per-request reset, parse exactly one X-WR-Modern:1
header, permit only POST start_apply.htm with no URL query, bind permission after
inherited auth before input/template dispatch. Guest CGI preflight rejects denied
transport before any secret access. Old production/Classic path unchanged.
A non-safelisted header requires browser CORS preflight across origins; pinned
server rejects OPTIONS501. This is a design dependency, not proven browser/auth
acceptance: full dispatcher/loopback auth exception/browser tests remain required.
Host checks verify pure policy, duplicate/malformed headers, generated anchor
ordering, denied transport no secret reads, complete request/commit/notify cases.
Actual target compile pending. Freshness and external-writer races remain open.

## Actual HTTP dispatcher host acceptance — 2026-11-10

Complete actual handle_request now executed under ASan/UBSan with controlled
auth/login/body/output hooks. Method/route/query/header duplicates/OPTIONS501
and reset pass. Marked Modern main/Guest apply requires auth even inherited
local state1; Classic exception preserved. Denied main/Guest transport reaches
no secret reads.24 complete request/commit/notify cases and171-field injection
still pass. Auth algorithm, real body/template/NVRAM combined HTTP requests,
browser sockets and freshness/external-writer synchronization remain open.
Publishedb6a8a0c; target compile pending. No production Apply or device acceptance.

## CGI duplicate/escape/body audit — 2026-11-10

Pinned CGI set_cgi replaces previous values, including aliased percent-encoded
keys; init_cgi splits raw ampersand/semicolon then decodes each assignment.
Added modern-form.h component: canonical-name duplicate rejection, strict escape
pairs and no decoded NUL, no raw controls/semicolon, nonempty complete fields,
exactly one Modern version marker,8KiB/64-field limits for current credential/
Guest forms. Pure ASan/UBSan checks pass. NOT yet bound to actual body input;
Content-Length consistency still required. Legacy unescape overlapping strncpy
and unchecked sscanf must be addressed in isolated candidate before executing
actual CGI parser under sanitizers. Production Apply remains unavailable.

## Actual marked body and CGI integration candidate — 2026-11-10

prepare-modern-body.py extends isolated HTTP source: single canonical decimal
Content-Length1..8192, no Transfer-Encoding, exact body read, modern-form
validation before existing init_cgi; reject before output and clear failure
buffer/cache. After successful template output, clear CGI cache/full post_buf.
Actual authenticated HTM MIME input binding verified. Candidate CGI valid percent
copy uses memmove(s,s+2,strlen(s+2)+1), fixing overlap AND old tail over-read.
Malformed Modern escapes are rejected before reaching legacy unescape; no claim
that all malformed legacy Classic input is repaired. Actual marked input/CGI
ASan/UBSan fixture passes decoded delimiters, spaces, duplicates/aliases, bad
escapes/NUL, short/zero/oversize and wiping. Valid Classic decode retained.
Dispatcher and body/CGI still separate fixtures, not combined endpoint/socket
acceptance. Target compile, freshness and physical results pending.
