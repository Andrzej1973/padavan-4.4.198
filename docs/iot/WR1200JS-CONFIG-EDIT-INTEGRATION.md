## Current executable chain traced — 2026-11-21

| Boundary | Current implementation | What the boundary proves |
| --- | --- | --- |
| HTTP view/edit | http-handler.inc, http-view-request.h, http-edit-request.h | Checks login/method/content type/CSRF; clears request body; edit reply means queue acceptance only |
| Typed submission | control-client.c: wr_iot_rc_submit_edit | Carries revision, key action and operation through the existing mailbox |
| Outer RC admission | control-server.c | Dispatches edit execute/progress/terminal hooks under existing operation ownership |
| Revision and KEEP/REPLACE | config-edit-server.c: execute | Claims retained lease under service guard, resolves fields in RC, routes RAM/AUTO/EXPLICIT/runtime separately |
| Save operation | config-save-server.c → config-save-owner.c | Retained save owner and terminal readiness; registration requires snapshot/readback capabilities |
| Native persistence | flash-worker.c → flash-save-attempt.c → flash-save-native.c | AUTO observes nvram_manual; native commit attempted through checked ioctl; separate flash readback determines durable outcome |
| Fresh terminal observation | config-edit-server.c: wr_iot_rc_edit_observed | Uses exact transaction identity and corresponding backend observer after completion |
| Target linkage | compile-runtime-link.sh | Already requires edit/view registration symbols and HTTP submit symbol; rejects unresolved IoT references |

This trace rules out adding another submit API or save facade as the next step:
those paths already exist. Next review native ioctl serialization against other
NVRAM writers and loaded-generation promotion. Trace actual prepared startup and
capability evidence alongside the existing runtime report before changing its
false flash/loaded acceptance fields. The public view and HTTP accepted response
must never be treated as a flash receipt or a loaded ra2 credential receipt.

## Current integration checkpoint — 2026-11-21

Hybrid Modern settings/apply resumed by the owner on2026-11-20; IoT remains
first. Older pause/unpublished/next-step statements below are historical.
Do not infer current absence of an implementation from those statements.

Source recheck on main14ef311c finds saved-config-store.c, config-save-server.c,
flash-save-native.c and native-flash-reader.c. The save facade registers only
when both native readback and snapshot capabilities are verified. Native save
uses the checked WR_NVRAM_IOCTL_SAVE_PROFILE path outside PID1; it is not an
unconditional HTTP NVRAM write. prepare-runtime.py stages save/edit/view startup
and reports HTTP route binding separately. Those sources do not by themselves
prove durability, loaded-profile promotion or main-image installation.

The runtime report still explicitly sets configuration_flash_bound=false and
configuration_loaded_promotion_bound=false; package-candidate-pair.py requires
both false. Do not flip these fields to claim completion. Next trace the actual
edit-view HTTP → typed mailbox → RC edit owner → store/save → fresh observation
chain and its loaded-generation handoff. Reconcile implemented pieces before
adding another facade. Verify native writer arbitration, KEEP/REPLACE revision,
manual/automatic save outcomes and retained old-generation shutdown identity.
Only then change the manifest contract with source, target and image evidence.
Optional1451 proves prepared FT TUs, not this configuration acceptance.
No router state changes are authorized.

# IoT configuration editing integration draft

The local candidate now includes guarded RAM/AUTO/EXPLICIT edit CGI routes and
an optional Classic form preparer. The latter requires the exact pending page,
verified native capability metadata and authenticated edit routes before writing
the form/script. It remains a candidate preparer, not main-image promotion.
DOM tests verify explicit reads, KEEP/REPLACE, three endpoint policies, queue vs
terminal status, clearing the password field and no automatic POST replay after
uncertainty. Browser rendering, localization beyond the draft Ukrainian labels,
full target/image assembly and physical acceptance are still required.

The RC private status observer now checks the retained edit facade before the
ordinary Save/RAM observers. Its focused runtime test verifies edit success
uses its own observer without falling through, while old status paths remain.
`check-config-edit-suite.py` runs the combined focused host suite with optional
pinned native inputs; its current run is not a target or device verdict.

HTTP view preparation now adds authenticated `wr_iot_view.cgi` with the existing
one-shot body input and no-cache JSON response. It accepts only POST with exact
form MIME and a canonical token-only CSRF body. Auth/method/MIME/token/length or
duplicate-field failure consumes/wipes the body and never calls private IPC.
The actual client uses the fixed view directory and production PID1/UID0 peer.
Unavailable or malformed private responses produce only an unavailable error.

The public JSON renderer validates the view, escapes quotes/backslashes and HTML
metacharacters, and has no password/hash/PMK field. Configured versus absent and
desired enabled state are explicit; neither enabled nor key_present proves a
loaded radio profile, associations or flash persistence. Independent Python JSON
parsing verifies UTF-8, escaped metacharacters, maximum SSID and exact field set.
Handler tests cover one-shot consumption, auth/POST/MIME/CSRF and unavailable/
malformed/absent responses. Actual client fork/endpoint tests preserve outputs
after refusal/path replacement. Pinned native HTTP preparation verifies exact
authenticated board-scoped route, all headers and metadata-capture execution;
repeated installation refuses without modifying files.

RC/HTTP view client and transport source staging compiles under host GCC with
native capabilities 0/1. Source metadata distinguishes HTTP view from unfinished
edit POST/full form integration and keeps target/runtime/production acceptance
false. The runtime-link artifact now retains this separate metadata. Classic
form, HTTP edit parsing/submission and final MIPS/image/device checks remain open.

The concrete RC view service is now source-staged in `config-view-runtime.c`.
It uses the fixed control-directory/view path, private0700 directories and the
existing owned socket lifecycle. It retains a separate parent-directory fd and
checks both held and named parent identity; a symlink/replacement cannot keep a
previously valid child path authorized. A retained or foreign socket is never
overwritten. Initial failures retry no more often than once per second;
detected identity loss disables the service and closes only owned descriptors.
Views use a server-selected120-second lease. Service close affects this IPC
endpoint only, not network OFF, DMA completion or execution cancellation.

`check-config-view-runtime.py` passes actual RC wait/endpoint/channel tests for
explicit readiness-gated installation, normal child query, repair after unsafe
parent permissions, pre-existing foreign socket preservation and parent-path
replacement by a symlink. Capture is an actor; actual edit/store composition is
tested separately. The source preparer now emits startup attempts in this order:
init_router → Save backend → edit backend → view runtime → optional boot arm.
Native capabilities and runtime admission can refuse installation; ordinary
boot still proceeds. Literal startup/physical-stop preparation and isolated
staging checks pass for both boards, policy gates and native capability cases.

`iot-edit-view-source.json` records prepared startup attempts and capability
evidence separately from HTTP, target and runtime acceptance, which remain false.
HTTP/Classic integration and end-to-end target/image/device validation remain
unfinished. These local edits are not covered by the published hotfix CI runs.

The RC wait loop now supports an explicit once-only, PID-bound view-service
registration with nonblocking init/readiness/timer/step callbacks. It polls the
existing status endpoint and separate view descriptor together. View callbacks
cannot run ahead of pending vendor notification/alarm handling, and timed view
work cannot delay the existing 100ms transaction progress. Fork-inherited hooks
are inactive. The prepared startup attempts are described above.

`check-rc-view-scheduling.py` links the actual RC wait loop, filesystem mailbox,
status endpoint and view transport. It passes registration/refusal/copy gates,
real child view requests while RC is idle, pending-signal wake without view work,
idle connection expiry and preservation of continuation counts. Its capture
callback is an actor. Original RC runtime and scheduler-composition regression
tests also pass. The concrete service binding is described above; HTTP and
firmware/device verification remain unfinished.

The view path now reuses the existing endpoint's PID, directory/socket inode,
mode, descriptor identity and owned-close checks through typed dispatch hooks.
Original status APIs wrap the same logic and retain their original wire
protocol. `config-view-endpoint.c` supplies the separate view callback and
keeps the candidate response private until pathname identity and both closes
have succeeded. An error leaves the caller's view/reference unchanged.

`check-config-view-endpoint.py` passes real fork/listen/query tests for configured,
absent and refused views. A server-side pathname replacement after capture
causes the client to refuse the response and cleanup preserves the foreign file.
The original endpoint ownership/descriptor tests and RC wait/status regression
also pass. Source staging copies view transport/endpoint units and headers to
RC/HTTP, without listening on a view path or installing an HTTP route yet.
Concrete path/startup preparation is described above; HTTP integration remains open.

`config-view-channel.c` now implements a separate connected Unix SEQPACKET
view protocol: a 36-byte WIQ1 query and fixed 168-byte WIV1 reply carry a fresh
32-byte nonce, explicit success, opaque reference and public fields only.
There is no password slot or native-structure serialization. Exact peer PID/
UID, socket type/family, magic, size, nonce, token, flags, string padding, UTF-8
and subnet checks gate output. The client uses a bounded one-second wait and
leaves outputs unchanged on refusal, malformed reply or timeout.

`check-config-view-channel.py` passes real fork/listen/connect tests for
configured/absent views, callback refusal, bad token/padding, nonce/magic/size/
flags corruption, timeout and wrong PID/UID. Eight malformed-request cases
verify no capture callback for invalid size/magic/zero nonce, missing callback,
invalid lifetime/UID or stream sockets. Existing status protocol is untouched.
Endpoint path ownership/lifetime, RC scheduling and HTTP binding remain open.

`wr_iot_rc_submit_edit()` now accepts edited fields, the RC-issued reference,
mode and key intent. It generates fresh request ID/time itself, mirrors that
identity into the typed payload, uses the original single mailbox and notifies
RC only after releasing the queue lock. Shared submission wipes the complete
private record on success and failure. The eight real composition scenarios
now enter through this client API; wrong/null references, mode and KEEP carrying
a key refuse without changing the output ID. Queue roundtrips verify all three
modes and exact inner/outer identity. Legacy Save transport and status-core
checks pass after factoring the shared submission helper.

The next private view channel must be distinct from read-only status queries:
opening a view creates/replaces an RC edit context. Use a peer-validated Unix
SEQPACKET request with a fresh nonce and a bounded reply containing only the
public view and reference. Preserve status query semantics. Require exact PID/
UID, type/length/magic/nonce and zero-padded field validation, bounded timeout,
unavailable replies that leave output unchanged, and real fork/socket tests
before adding an HTTP-facing client. The connected transport is implemented
above; endpoint ownership and an HTTP-facing client are not installed yet.
## Current local implementation boundary

`config-edit-server.c` composes the real edit lease/pin/view with the existing
RC RAM and Save facades. Its private read API uses CLOCK_MONOTONIC and the
existing nonblocking kernel entropy helper, refuses active/pending/radio-owned
work, and retains at most one view. A fresh read supersedes its previous view.
It never holds the service guard while waiting for the browser.

On execution, the shared queue already owns shutdown admission. The edit facade
holds the same service guard across fresh revision checking, KEEP/REPLACE
resolution and admission to the existing configuration/save owner. It creates no
second NVRAM or flash writer. It retains exact transaction identity for progress,
terminal cleanup and observation; terminal retries never redo resolution or
execution. An old reference cannot release a newer live view. Unknown Save
outcomes retain the original shared admission/owner and cannot start another
write. Service-guard guarantees do not establish atomic exclusion of arbitrary
outside native writers that ignore that guard.

The source preparer stages the new RC unit/headers and startup attempts, but
does not expose the view over HTTP yet. Installation requires verified native
snapshot and readback capabilities. Exported private Save facade entrypoints
reuse its original owner and validation. HTTP/private view IPC, HTTP submit binding,
Classic form, target/image checks and device acceptance remain
unfinished. Modern stays paused.

`check-config-edit-route.py` passes eight isolated host scenarios, linking the
actual queue/client/server, edit facade, RAM facade, Save facade, configuration
owners, store/parser/service guard and fork worker. It covers KEEP into RAM,
confirmed flash, AUTO/manual RAM-only, changed record rejection, expired view,
unknown flash outcome without replay, first provisioning via REPLACE, and stale
form rejection followed by successful use of a newer reference. Status rejects
changed RAM after a completed edit. Native NVRAM/flash/SDK boundaries and clock/
entropy are actors; this is not router or target firmware evidence. Isolated
staging syntax checks pass with snapshot/readback capabilities 0/1, and the
previous Save facade tests still pass after exposing its private entrypoints.

The common RC server now has an independent once-only edit registration slot,
using the existing execute/progress/terminal callback shape. It copies callbacks,
binds them to the installing PID, and refuses incomplete, duplicate or active/
pending/radio-owned registration. No production edit facade is installed yet.
Unregistered edits remain REJECTED, including when ordinary Save is registered.

Registered edit operations use the existing single continuation and publication
retry. RAM edit accepts only RAM success; AUTO/EXPLICIT edit can complete as RAM
or flash. APPLIED is never edit success. Mailbox terminal-kind validation matches
these rules. A wrong result retains recovery without reexecuting the request.
The extended real-filesystem queue test uses injected edit callbacks: all three
modes execute once, failed terminal readiness retries publication without another
progress/write call, RAM-to-flash success is refused, and a fork cannot invoke
the parent's callbacks. Legacy runtime/config/Save checks and the literal
dispatcher compile regression also pass. See the current boundary above for
the subsequently implemented store/save handoff and remaining integration.

`config-edit-lease.h` now adds the bounded read-context lifecycle around the
same desired pin. A caller-supplied checked entropy provider must return exactly
32 bytes; the reference uses 128 bits and rejects a zero reference. Production
binding must use the existing nonblocking kernel entropy helper, never browser
input or a predictable fallback. The caller supplies RC monotonic seconds,
not a request timestamp. Requested lifetime is 1–300 seconds with overflow
rejection. HTTP/UI policy chooses the duration within that cap.

Only the original LIVE context can claim once. Expiry, clock regression or a
failed matching-reference resolution invalidates it permanently until explicit
release; a later successful read cannot revive it. A foreign reference refuses
without invalidating the real context. Release wipes private observation memory
only, including CLAIMED contexts: it neither cancels an execution owner nor
authorizes reexecution. The RC facade must retain its existing queue/admission
discipline while handing the resolved candidate to the real configuration owner.

`check-config-edit-lease.py` links the actual store, pin, snapshot parser and
service guard under ASan/UBSan. It checks short/error/zero entropy, excessive
lifetime, deadline overflow, duplicate open, wrong reference, copied context,
one claim, expiry without revival, clock regression, native read error and
complete context wiping. These tests perform no SET. Read endpoint, production
entropy/clock binding and guarded execution handoff remain pending.

`config-edit-record.h` adds a separate `WR-IOT-EDIT-1`
codec for transaction ID/time, opaque revision ID, RAM/AUTO/EXPLICIT mode,
KEEP/REPLACE intent and complete edited fields. Canonical lowercase hex
preserves UTF-8 and delimiters. KEEP requires the entire password array empty;
REPLACE validates its supplied key. Both desired ON and OFF require complete
SSID/private subnet data. The common request envelope now maps this version to
three distinct edit operation kinds; existing runtime/config/Save wire formats
retain their bytes and meanings. Until an edit backend is registered and tested,
RC rejects every edit operation and publishes REJECTED without retaining shutdown
admission or calling any existing runtime/config/Save executor.

The maximum serialized record is bounded by 438 bytes: 14 header bytes,
66 ID bytes including newlines, 21 timestamp bytes, 9 mode bytes, 8 intent
bytes, 2 enabled bytes and 318 bytes for hex fields/newlines. It fits the
existing 512-byte mailbox record limit. Host ASan/UBSan tests cover the maximum
valid private subnet/SSID/PSK lengths, all modes/states, every truncated prefix,
embedded NUL, invalid version/mode, hidden KEEP key bytes and short output.
The encoded replacement key is still secret private queue material; this is
not the public view or a browser read response. The actual filesystem queue
and RC rejection path are tested by `check-save-transport.py`, including all
three edit modes while Save hooks are already registered. Existing record,
RAM/flash mailbox and Save registration/continuation checks also pass. The
literal dispatcher and isolated runtime staging compile checks pass. Execution
binding, a submit API and target validation of this local draft remain pending.

Local implementation: `config-edit-pin.h` now composes the actual desired pin
with nonsecret view projection and KEEP/REPLACE resolution. Capture rechecks
fresh native state before exporting a view; drift releases the new pin and
leaves output unchanged. Proven absence exports an empty view and permits
only a complete REPLACE candidate. Resolution is read-only and does not consume
the future queued operation or perform a store/save.

`check-config-edit-pin.py` passes with native snapshot capability both disabled
and enabled, linking the actual store, service guard and snapshot parser under
ASan/UBSan. Native NVRAM calls are actors. Cases include error/drift during
capture, duplicate capture, wrong ID/time, copied/forked pin, changed key,
read failure, proven absence and later record appearance. No SET is permitted
by the fixture. Endpoint, expiry and guarded execution admission remain open.

The current Save endpoints submit complete provisioning records. They do not
implement a read/edit form, implicit password retention or a browser revision.
Modern development stays paused; this plan covers the required Classic IoT
configuration path only. It authorizes no router action or driver change.

## Reuse the actual desired revision owner

`saved-config-store.c:wr_iot_generation_config_capture()` already captures one
complete tuple under a caller-held service guard. It binds retained bytes to
the current PID, object address, request ID and creation time. Its `current()`
checks fresh native state without retargeting the captured revision; release
wipes the private storage. Reuse this mechanism in the RC edit transaction
instead of adding a second private snapshot owner with different rules.

The read transaction must acquire the existing guard, generate an opaque
unpredictable ID through a checked entropy path, capture exactly once, then
project `config-view.h` from those same retained bytes. A missing tuple is
proven absence, not permission to copy an old loaded profile. Capture/read
failure must produce an unavailable result and no editable-success response.

Keep the pin private to RC. The browser receives its nonsecret ID and public
fields only. Never send the canonical record, password, password hash, PMK or
an encoding of any credential. The view structure is not a wire format.
Text serialization and HTTP auth/CSRF requirements remain explicit work.

## Edit submission and lifetime

Bind the form's ID to the retained pin, current PID/object and creation time.
Under the existing configuration/service admission, call the actual revision
`current()` before using any captured key. Resolve KEEP/REPLACE through
`config-edit.h` against that exact captured record. KEEP accepts no password
bytes; REPLACE requires a complete valid replacement. Absence cannot KEEP.

The queued edit must retain its expected revision until the configuration owner
accepts it. Resolving a password in HTTP and later submitting an unconditional
complete record would lose the revision check and is insufficient. Extend the
typed queue/RC operation to carry the opaque edit reference and field intent;
perform resolution in RC immediately before the existing guarded store/save
transition. Review native writers that bypass the service guard before claiming
atomic protection against all outside NVRAM writers.

Use a bounded retained read transaction with explicit invalidation/release.
Define expiry, repeated reads, concurrent tabs, lost responses, shutdown and
process restart behavior before endpoint activation. Never silently recapture
a changed record under an old browser ID. Consumed requests must not resolve
or execute twice. Uncertain store/save ownership follows existing recovery.

## Required evidence

Compose the actual native snapshot parser, desired pin, service guard, view,
edit resolver and real configuration owner in host tests. Cover absent/error,
changed key/SSID/subnet, copied/forked owner, stale token, KEEP/REPLACE, concurrent
reads and pending shutdown. Verify authenticated HTTP parsing/serialization,
secret-free responses and typed queue continuation separately. Then require
MIPS RC/HTTP compilation, assembled page/API inspection and authorized router
acceptance. Pure view and resolver tests alone do not satisfy these gates.
