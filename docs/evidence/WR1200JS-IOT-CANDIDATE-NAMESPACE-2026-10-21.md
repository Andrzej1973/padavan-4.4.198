# WR1200JS IoT request candidate namespace — 2026-10-21

The candidate `wr_iot_request_stage()` previously read `wr_iot_enable`,
`wr_iot_ssid`, `wr_iot_psk` and related active-form keys. The authenticated
Padavan Apply path writes submitted registered values before a later RC action
can report activation success. Reusing the active names in a future IoT form
would therefore expose a failed request as changed live configuration.

`tools/iot/request-stage.c` now maps only seven explicit fields to
`wr_iot_request_enable`, `wr_iot_request_ssid`, `wr_iot_request_psk`,
`wr_iot_request_gateway`, `wr_iot_request_mask`, `wr_iot_request_start` and
`wr_iot_request_end`. Unknown fields are refused. The validated immutable
request still stages to the existing temporary `*_t` gates; the active keys
are not written by request staging. The future authenticated form must submit
only this candidate namespace, with a fixed Apply action and explicit cleanup
after success/failure.

The two host fixtures were updated to use candidate names. The stage fixture
also retains distinct active enable/SSID/password values and checks them
after successful staging. On Windows, the staging fixture passed under
MinGW GCC with minimal host networking declarations. The snapshot fixture
passed using a temporary copy that mapped the Linux-only test descriptor
`/dev/null` to Windows `NUL`; the repository fixture and production source
were unchanged by that adaptation. Both compiled with
`-std=gnu11 -Wall -Wextra -Werror -O2`. The first unadapted snapshot attempt
failed at its `/dev/null` descriptor probe on Windows; that is a host-test
path issue and not a router result. The temporary probe directory was removed.

This change is local and uncommitted. The IoT candidate RC source is still
excluded from production firmware, and no HTTPD/RC notification handler,
activation backend, complete dnsmasq rollback or device runtime has been
implemented or verified. IoT must remain OFF/unavailable in shipped images.

## Windows fixture follow-up

The snapshot fixture now selects Windows `NUL` under `_WIN32` and Linux
`/dev/null` otherwise, so the test source itself no longer needs a temporary
path substitution. `git diff --check` passed for the three changed IoT C files.
The fixture was **not rerun** after this edit: the Codex executor denied access
inside newly created probe directories, both under the Windows temporary
folder and the workspace parent, before compilation. The two empty directories
are `C:\Users\ANDRZEJ\AppData\Local\Temp\wr-iot-snapshot-fd9j0p9d` and
`C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\wr-iot-snapshot-ub1y6vi7`.
Removal of the latter was also denied. They contain no key, firmware or test
output. A later authorized executor should remove these exact directories and
rerun the snapshot fixture without changing the production source.

The changed fixture itself subsequently passed a no-output-file MinGW syntax
check (`gcc -std=gnu11 -Wall -Wextra -Werror -fsyntax-only
tools/iot/check-request-snapshot.c`). This checks C syntax, not the linked
snapshot/request-stage behavior; the full fixture rerun is still outstanding.

## Active-gate refusal follow-up

`wr_iot_request_stage()` previously refused an existing `br-iot` but could
still clear temporary service state when the bridge was absent and one of
`wr_iot_profile_t`, `wr_iot_network_t` or `wr_iot_firewall_t` remained open.
That can occur during partial activation or recovery. It now refuses any
nonzero or malformed service gate before reading the candidate or writing
anything. The host stage fixture now starts from three closed gates and checks
that both `1` and malformed `stale` values for each gate cause refusal with
zero writes. The fixture source passed MinGW `-fsyntax-only` with warnings as
errors, and `git diff --check` passed. Full linked execution remains unverified:
MinGW lacks Linux `<net/if.h>` and this executor cannot create/access a
temporary compatibility include directory. No production image includes this
candidate change yet.

## Full host fixture rerun and probe cleanup

A later retry used a controlled `.host-probe` directory inside the existing
repository tree, with minimal Windows compatibility declarations for
`net/if.h`, `arpa/inet.h` and `rc.h`. MinGW compiled both the stage and
snapshot fixtures with `-std=gnu11 -Wall -Wextra -Werror -O2`; both executables
returned exit 0 and printed their `PASS` lines. The stage run includes the new
active/malformed gate refusal cases, and the snapshot run uses the repository's
portable `NUL` fixture code directly. The controlled probe directory and its
executables were removed after the checks. The two older empty directories
listed above were also removed using the approved elevated command after
confirming their exact paths and that both were empty.

This supersedes the earlier temporary-directory and linked-execution limits
for these **host fixtures**. It does not supply a production HTTPD/RC caller,
target firmware inclusion or physical-router acceptance.
