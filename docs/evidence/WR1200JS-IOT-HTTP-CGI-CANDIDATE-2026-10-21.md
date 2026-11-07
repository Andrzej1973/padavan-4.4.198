# Dedicated IoT CGI source candidate — 2026-10-21

## 2026-10-29 source-preservation guard

`prepare-http.py` now compares every existing `wr-iot` header against the
intended candidate before writing any source file, and refuses linked header
or validation destinations. An isolated temporary-source fixture with a
conflicting `http-form.h` returned the expected refusal; the existing header,
`httpd.c` and `web_ex.c` bytes stayed unchanged, and no later candidate
header was created. Python compilation and targeted diff check passed. This
protects local drafts during candidate preparation; it does not install the
CGI or prove runtime behavior.

## 2026-10-29 exact disabled form

The URL-encoded parser now accepts a disable request only with `enable=0`
and the CSRF token. It rejects extra SSID or password fields instead of
silently discarding them before the RC request. Strict C11 form fixture
passed with both negative cases; isolated positive HTTP preparation installed
the updated header and all three authenticated routes. The broader request
fixture requires POSIX `arpa/inet.h` and could not compile with local Windows
GCC; Linux CI/target coverage remains pending. No image or router change.

## 2026-10-29 HTTP login lifetime

The candidate CSRF token and pending POST body were process-global and did
not follow the stock HTTPD login reset. `prepare-http.py` now binds an IoT
session reset to `reset_login_data()` under `BOARD_WR1200JS`; the handler
clears the token, body and body length. This covers the existing logout,
timeout and reset paths that call that stock function. An isolated positive
HTTP source preparation and extracted-source check passed, and the handler
fixture now contains a logout/reset replay rejection. Python compilation
and targeted diff check passed. The handler fixture was not executed on
Windows because its POSIX request dependencies need Linux headers; Linux
CI, target link, real-session behavior and production installation remain
unverified.

Negative source checks also passed: a second preparation refused without
changing HTTPD/WebUI bytes, and removing the login-reset call from an isolated
prepared source made `check-http-source.py` reject it with the expected
session-state diagnostic. These checks do not execute the HTTP session.

## Follow-up: source binding and board selection

`prepare-control.py` now installs mailbox/client objects into HTTPD and
mailbox/server objects into RC, both under the WR1200JS Makefile condition.
It adds one exact `wr_iot_apply` notification branch before the existing
reboot branch, preserving that branch and the rest of the notification chain.
CGI implementation/routes and HTTP request metadata are now guarded by
`BOARD_WR1200JS` as well, avoiding routes with absent objects on other boards.
The report explicitly records that the activation backend is not installed
and that the candidate is not production-ready or runtime-verified.

The GitHub connector supplied the pinned upstream HTTPD Makefile
([source](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/httpd/Makefile),
blob `8d6ba5e78828b9e7b9385fde030fee7c67fb75fa`) and RC main
([source](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/rc/rc.c),
blob `340b3e5a3ca1466bfcc2a00cb799d3a81b0ef37e`). The local fixture combined
these with the local base-web-ref HTTP snapshot and previously prepared
iot-rc-stage-fresh RC Makefile. It is not a final assembled firmware tree.

`check-control-source.py` compared installed source units with their intended
transformations and invoked real GNU Make on both installed Makefiles, with
empty board/cflags include fixtures and three explicit CFLAGS selections:
WR1200JS, another board, and none. Only the first selected channel objects.
The generated fixture contains the actual inserted notification branch.
Strict MinGW compile/execution passed with and without the WR1200JS define;
exact-event matching and continuation to the retained reboot branch passed.
These are call-counter fixtures and execute no reboot or service operation.
Installed metadata extraction/execution and Python syntax checks passed.
Repeating source preparation was refused; the RC source hash was unchanged.

ABI now stages these source bindings and schedules installed-object MIPS
compilation in addition to earlier original-source probes. Linux filesystem/
channel runtime, MIPS compilation, target linking and final-image/device
acceptance have not been run for these local changes. Production workflows
still do not invoke this candidate preparation. Next implement the strong
`wr_iot_activation_execute` dependency with actual guarded startup, complete
rollback, observed state and safe persistence; transport binding alone is not
an operational IoT feature. Temporary fixture files were removed.

## Follow-up: private mailbox and HTTPD/RC adapters

Candidate implementations now exist in `control-mailbox.c`, `control-client.c`
and `control-server.c`. The fixed integration path is
`/var/run/wr-iot-control`, with a 0700 owned directory, a persistent exclusive
lock, 0600 single-link regular records, no-follow/nonblocking opens and checked
directory/file identities. Request/result publication uses exclusive temporary
files, fsync and rename. A failed or uncertain publication retains blocking
state rather than accepting another request or inferring activation success.

Only a matching queued record can be claimed. Claim first publishes RUNNING;
interrupted RUNNING or RECOVERY requests cannot be replayed or replaced.
Queued requests older than 30 seconds are rejected before execution. RECOVERY
can become REJECTED only after a caller confirms rollback. Terminal credential
cleanup can retry without invoking activation again. Status and submission use
the same mailbox lock; RC releases it before acquiring the distinct service
guard through its eventual activation backend, so status can observe RUNNING.

`wr_iot_rc_submit` generates a random ID, serializes/copies the validated request,
publishes it and sends only fixed `notify_rc("wr_iot_apply")`, with no credentials
in argv/logs. `wr_iot_rc_status` reads only an ID-matching result. The dispatcher
claims once and calls the strong, still-unimplemented `wr_iot_activation_execute`
backend. Unknown backend outcomes require recovery. The transport does not
implement activation or prove that any saved setting became effective.

Local verification: strict MinGW `-fsyntax-only` passed for the mailbox, client,
server and fixture sources using temporary POSIX **declarations** plus a Windows
socket-header adapter. No filesystem/lock/channel runtime test ran locally;
the declarations do not verify Linux system-call behavior or target ABI/linking.
The probe files were removed. The ABI workflow now schedules actual Linux
sanitizer execution of mailbox/channel fixtures and MIPS object compilation,
including the client's real pinned `notify_rc.h`; those results are pending.

The Linux fixtures cover lock contention, ID binding, duplicate notifications,
retained recovery, queued expiry, directory/file modes, symlink/hardlink refusal,
and failed publication with an existing temporary record. Channel execution uses
a fake activation backend and cannot establish device behavior even after it
passes. Next install/link these adapters into candidate HTTPD and RC sources,
register only the fixed RC notification branch, and implement the real guarded
activation/rollback backend. Production preparation still excludes IoT.

## Follow-up: request records and observed-result route

`control-record.h` now defines a bounded versioned request format with an exact
field count, lower-case hex request ID and checked decimal monotonic timestamp.
It encodes fields explicitly and validates decoded credentials/subnet structure;
it does not serialize native structs, pointers, padding or byte order. Malformed
records leave the output untouched. Disabled records must contain no hidden
SSID/credential/subnet fields. Record bytes contain a password and must be
transported only through the planned private owned channel, never logs or argv.

The source transformer additionally registers authenticated `wr_iot_result.cgi`.
It requires a safe session and a valid ID, then accepts only an ID-matching
backend observation with a known state and coherent monotonic timestamps no
older than 30 seconds. Missing, stale, future or mismatched results produce
`unknown`. States are `queued`, `running`, `applied`, `rejected` and
`recovery_required`; queue acceptance cannot be rendered as `applied`.

Strict MinGW record and extended CGI fixtures passed, including malformed/
unterminated records, delimiter injection, disabled secret fields, timestamp
overflow, stale/future/mismatched results, and pending/recovery distinctions.
Metadata extraction and its executable still pass. ABI now also schedules the
record fixture under Linux sanitizers and MIPS compilation; these CI results
remain pending. The Windows socket adapter and executables were removed.

The result reader `wr_iot_rc_status` is still an external dependency, alongside
submission. Actual private transport storage/ownership, RC notification and
execution, recovery retention, live result observations and real activation
remain unimplemented. Local `wsl --list --quiet` returned installation/help
output and exit 1, so no local WSL/Linux execution was established.

## Implemented source path

`tools/iot/prepare-http.py` prepares a separate HTTPD source candidate with
exact authenticated routes `wr_iot_token.cgi` and `wr_iot_apply.cgi`. It adds
per-request method and Content-Type observations to `httpd.c`, then installs
`http-handler.inc` before the existing MIME handler table in `web_ex.c`.
The existing authentication check precedes body input; the handler separately
requires a safe login session and the server-owned CSRF token.

The input callback reads only the bounded POST body and does not use generic
Apply/NVRAM processing. Duplicate Content-Type headers are rejected. Metadata
resets for each request. Independent header capture preserves the original
multipart boundary parser. Rejected or consumed body buffers are cleared;
responses contain no submitted credentials. Successful transport submission
can return only `accepted` with a bounded hex request ID, never `applied`.

The HTTP side validates structure, credentials and internal subnet consistency.
It intentionally supplies no assertion about current router/radio mode or live
route overlap. RC must repeat those checks with live values while holding the
service guard before staging or mutation. `wr_iot_request_stage_from()` is the
available guarded input path for that part of integration.

## Verification performed

- Prepared the candidate from the owner's local `base-web-ref` HTTPD source
  snapshot; this does not establish that the local snapshot equals the final
  prepared firmware source. CI is configured to repeat against its pinned source.
- `check-http-source.py` verified exact routes with `need_auth=1`, unchanged
  installed handler content and authentication-before-input ordering. It
  extracted actual inserted metadata code into a C fixture.
- Strict MinGW GCC compilation (`-std=gnu11 -Wall -Wextra -Werror -O2`) and
  execution passed for metadata and CGI handler fixtures. Metadata cases cover
  method/reset, missing/duplicate/empty MIME and retained multipart boundary.
  CGI cases cover valid queue acceptance, unsafe login, GET, missing/wrong MIME,
  wrong CSRF, truncated/oversized bodies, consumed-body reuse, backend refusal,
  and absence of credentials/activation-success claims in the response.
- The CGI fixture uses a temporary Windows Winsock header adapter for the
  existing subnet validator. This is host evidence; no Linux HTTP server,
  target HTTPD binary, real RC transport or router was executed.
- Both Python source files parsed successfully. The ABI workflow now schedules
  candidate source preparation, Linux sanitizer fixtures and MIPS fixture
  compilation. These additions have not run in CI for the local revision.

## Remaining production dependency

The source deliberately declares, but does not implement, `wr_iot_rc_submit`.
Its implementation must copy the request before returning, own a bounded,
serialized inter-process submission, and return a valid request ID only after
queue acceptance. A separate authenticated result path must report observed
activation or retained recovery. RC still needs complete real radio, DNS,
bridge and firewall activation/rollback callbacks and persistence handling.

The firmware preparation workflow does not call this candidate transformer.
No production endpoint, IoT enablement, firmware build, commit, push or router
change occurred. Keep production IoT excluded until complete source/image and
device acceptance gates are satisfied.
