# Modern POST candidate checkpoint — 2026-11-11

This is isolated verification source. Production Modern remains read-only.

The candidate extends existing authenticated start_apply.htm and its CGI/NVRAM
pipeline. Marked requests require POST, one custom header, no URL query, actual
authentication even in trusted-local login state, one canonical positive decimal
Content-Length1..8192 and no Transfer-Encoding. Full body length, unique decoded
field names, valid escapes and one Modern version marker are checked before CGI.
The existing valid-percent decoder uses memmove with the source-tail length.
CGI cache and body are cleared after successful output; failed input is wiped.

The joined host fixture executes actual HTTP dispatcher, body callback, CGI,
request/service loop, variable apply, commit and notify functions under ASan/UBSan.
It covers24 band/shared/manual/keep/change/open cases and whole-request replay,
UTF8/escaping, namespace injection, duplicate/short bodies and authentication
rejection. It substitutes authentication computation/login state, sockets,
NVRAM/flash/RC operations and template expansion (using the exact callback order
from start_apply.htm).171 actual WLAN names/types are included, but event bits
remain fixture constants. This does not establish device runtime or full HTTP
server acceptance.

Run `PYTHONDONTWRITEBYTECODE=1 python3 tools/webui-preview/check_guest_candidate.py
<exact-source-tar>` on one line against the preserved c25283e source archive.
`check_json.py` runs pure C components. Optional CI compiles/links the complete
isolated HTTP package and checks credential/Guest/body guard strings and ELF.
It never installs the candidate or changes the production image.

Open requirements before Apply activation: exact target result for this package,
request freshness/concurrency policy, real browser/HTTP/template behavior,
structured response and retry semantics, safe radio/driver lifecycle, complete
UI validation/confirmation/error flows and physical acceptance at the agreed
later stage. Never equate committed settings or notification with running Wi-Fi.

Evidence: WR1200JS-MODERN-ENDPOINT-HOST-2026-11-11.json and earlier BODY-CGI,
TRANSPORT and REQUEST-SEQUENCE reports. Earlier candidate target31e7732 was
verified independently in CI988-989 evidence; it does not cover this body change.
Temporary source/C/binary trees were automatically removed; no firmware retained.

## Local Guest snapshot precondition — 2026-11-11

Guest candidate now requires13 `wr_modern_guest_expected_<field>` values from
the previously displayed public Guest configuration. Exact selected-band NVRAM
comparison occurs before the secret read and all writes. Missing or changed
public values reject unchanged; no PSK is part of the posted snapshot.26 pure
missing/mismatch checks and a joined newer-SSID witness pass with zero secret
reads/writes/commit/notify. Old-body replay after a change is rejected; after a
lost response, reread configuration rather than retrying an old draft blindly.

This is an optimistic public precondition, not authorization or atomic CAS.
External writers may race between compare and persistence; secret-only changes
are not represented. Keep intent reads the current key at admission. Request-ID
ledger, coherent snapshot/concurrency policy, structured conflict response and
client integration are still open. Production Apply remains disabled.

### Guest rejection reason

Candidate admission now reports internal NONE/INVALID/RELOAD without changing
the owned-plan-on-reject invariant. Missing or changed public snapshot yields
RELOAD; the actual CGI candidate emits `Modern Guest snapshot needs reload.`
Distinct error counters in the joined fixture verify all24 stale replays and
the newer-SSID witness without writes or secret reads. This remains the Classic
HTML response with HTTP200, not a JSON/409 API. Structured result/retry handling
is still required. No driver/runtime success is implied by admission success.

## Isolated Guest JSON route

`prepare-guest-json.py` adds authenticated `wr_modern_guest_apply.json` only to
the isolated candidate. Same POST/custom-header/exact-body/CGI gates apply. It
uses the existing update/apply/commit/notify functions, directing legacy script
output to a sink. The result is fixed-schema JSON with no credential/SSID echo.

States: configuration_matches / reload_required / busy / rejected / unconfirmed /
unavailable. Successful RAM readback is not flash or radio acceptance: flash and
notification report requested_unverified, runtimeVerified is always false. Auto
retry is always false; reread configuration after a lost response or stale draft.
Applications use HTTP200; framing/auth errors retain server400/401 handling.

The candidate refuses pending HTTP changes and compares all13 public fields plus
the owned key after actual apply. A fault-injected partial write returns
unconfirmed/settingsMayHaveChanged, suppresses deferred commit/notify and does
not roll back RAM. This limitation prevents production activation until the
atomicity/concurrency policy is established. External NVRAM writers remain a race.

77 JSON replies pass strict schema/state checks through the joined actual host
HTTP/body/CGI/application chain, including stale replay, fresh no-op, invalid
fields, pending work, sink failure and a failed NVRAM write. Authentication
computation, socket, NVRAM/flash/RC and template expansion are substitutes. Real
browser/client integration and exact target result remain open; production
Modern still has no Apply. See GUEST-JSON-HOST and SNAPSHOT-HOST evidence.

## Client result and one-shot submission controller

Actual wifi.js now strictly decodes the nine-key JSON protocol and maps only
known observations to fixed Ukrainian messages. Spoofed runtime/flash/service
acceptance or malformed/extended responses become unknown. configuration_matches
never labels a running network.77 actual C endpoint replies agree with the client.

An opt-in guestSubmission controller permits exactly one transmit call. Pending
clicks and terminal replay are blocked. Transport errors and a15s default timeout
yield unknown; timeout aborts the signal and late replies cannot upgrade it. A
fresh controller must be created after configuration is reread. No request body,
error text or secret is placed in the public state or storage; this does not
claim secure erasure of JavaScript strings.

Production rendering does not instantiate this controller or expose Apply. Real
fetch/button/dialog integration is pending backend concurrency/lifecycle gates.
CI runs check_guest_client.js when verifying source revisions that contain it;
optional ancestor verification before this component remains supported. The
existing firmware workflow is already watched by the failure monitor.

## Real local socket and Edge checkpoint

`check_guest_candidate.py <source-tar> --browser-check` additionally launches a
loopback-only native C fixture and a separate attacker origin, then headless
Windows Edge with a fresh temporary profile. Actual pinned auth_check/b64_decode,
HTTP dispatcher, body/CGI/apply/commit/notify and actual client protocol run over
real local sockets. Credentials/login state, NVRAM/flash/RC, header/daemon/SSL
wrapping and template expansion remain fixtures. No router is contacted.

Same-origin update, UTF8, blocked double click, stale reload and wrong-password401
pass. A known-fixture-credential cross-origin fetch is blocked after actual
OPTIONS501: browser failure plus OPTIONS counter, unchanged POST/write counters
are verified. This does not replace production browser/daemon or device tests.
The Windows-specific browser check is opt-in and is not added to Linux CI.

Latest run inventoried and removed12270513 profile bytes and1688370 native/source
fixture bytes (27 files), about13.3MiB. Native server/attacker server stopped,
profile and source scratch confirmed absent. Durable source/fixtures/evidence
retained; no firmware stored. See GUEST-BROWSER-SOCKET evidence.
