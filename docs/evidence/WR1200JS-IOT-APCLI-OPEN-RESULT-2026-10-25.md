# AP-client open result is currently lost

Date: 2026-10-25. Source read only; no vendor driver, image or router mutation.
Examined the isolated `main-open-owner-v12-20261025` source candidate under
`.iot-local-check/`, which retains the AP-client path from the source driver.

## Source trace

1. `ap/ap_apcli_inf.c`, `ApCli_VirtualIF_Open`: increments the module pin,
   calls `VIRTUAL_IF_UP`, then registers HNAT (when configured), invokes
   `RTMP_AP_IoctlHandle(... CMD_RTPRIV_IOCTL_APC_OPEN ...)` without checking its
   result, and returns `0`.
2. `ap/ap_cfg.c`, the `CMD_RTPRIV_IOCTL_APC_OPEN` case, returns
   `NDIS_STATUS_FAILURE` when `ApCli_Open` returns false.
3. `ap/ap_apcli.c`, `ApCli_Open`, returns false if no matching AP-client
   `wdev.if_dev` is found. It starts the netdev queue and performs additional
   state changes before returning true for a match.
4. `ApCli_VirtualIF_Close` also ignores the `APC_CLOSE` ioctl result, calls
   `VIRTUAL_IF_DOWN` without checking its result, decrements the module pin and
   returns `0`. The ioctl handler can report failure when `ApCli_Close` fails.

## Consequence for the IoT radio owner

AP-client is another consumer of the same virtual interface count. The
isolated main/MBSS owner cannot be bound safely while AP-client can enter
`VIRTUAL_IF_UP` and report successful `ndo_open` after a failed `APC_OPEN`.
The matching close path may then release an unverified physical/virtual
reference. Merely adding an AP-client ticket before `VIRTUAL_IF_UP` is not
enough: the `APC_OPEN` result and its potentially partial state need an
explicit success/uncertain outcome and retained lifetime until checked
recovery. The same rule applies to `APC_CLOSE` and checked `VIRTUAL_IF_DOWN`.

## Required next step

In an isolated candidate, reserve an AP-client record and `AUX_START` or
`AUX_OPEN` ticket before count mutation, check `APC_OPEN`, and prove which
side effects can be rolled back. Keep module/adapter/netdev ownership on
uncertain failure; coordinate HNAT deregistration, AP-client teardown and
physical close through the same checked owner. Audit WDS/monitor peers before
production binding. This finding does not prove a live AP-client failure or
authorize firmware installation.

## Host reservation added

`tools/iot/virtual-open-claim.h` now has `wr_iot_aux_open_reserve`. Under the
adapter transition lock it chooses `AUX_START` for zero vendor references or
`AUX_OPEN` for a nonzero count, reserves the exact published device record,
and aborts an unmutated ticket if record reservation fails. It never invokes
the driver or changes the vendor count. `check-virtual-open-claim.c` exercises
wrong identity, count overflow, first-open reservation, duplicate admission,
subsequent open, stale ticket and reset fencing. Strict C11 compilation and
execution passed on the host. This is a prerequisite only; AP-client/WDS/
monitor wrappers and the shared dispatcher are not yet bound to it.

## Result policy modeled

`ApCli_Open` calls `wf_fwd_probe_adapter` when available before searching for
the matching AP-client device. Combined with the preceding virtual-UP call,
an `APC_OPEN` failure is not proof of an unmutated adapter. The host-only
`wr_iot_ref_complete_aux_open` therefore allows IDLE/pin release only when
neither virtual-UP nor family OPEN was attempted. AP-client and monitor record
OWNED only when both calls succeed; every other attempted path becomes UNCERTAIN_OPEN with the
module pin retained. The strict C11 interface-reference fixture passed for
APC failure after virtual-UP, early failure, full success, and a failed
virtual-UP attempt. This models the result; it does not yet provide the
required checked recovery owner or change the real AP-client wrapper.

WDS has no separate family OPEN: `WdsVirtualIF_open` invokes only virtual-UP,
then HNAT and queue setup. The result helper now has an explicit
`family_open_required` flag so WDS can become OWNED after checked virtual-UP
without a fictitious second call. WDS virtual-DOWN remains a void, unchecked
operation on close. The strict C11 fixture also covers WDS success and failed
virtual-UP. Monitor does have a separate `SNIFF_OPEN` ioctl, whose result is
ignored by `Monitor_VirtualIF_Open`. `Monitor_Open` itself currently returns
TRUE even when the supplied netdev does not match `monitor_wdev.if_dev`, so
its return value alone is weaker than an identity check. None of the three
wrappers is bound to the host result policy yet.

## Isolated monitor identity correction

`tools/iot/prepare-monitor-open-identity-candidate.py` pins the reviewed
monitor source by SHA-256 and emits a separate candidate under
`.iot-local-check/monitor-open-identity-v13-20261025/`. Its only driver
change makes `Monitor_Open` return FALSE for a nonmatching netdev and TRUE
inside the matching branch. A strict C11 host fixture compiles the exact
extracted function and passes both identities; a file diff shows only the
two return-line changes. The candidate is not installed in production. The
outer monitor wrapper still ignores `SNIFF_OPEN` status, so this correction
alone cannot make monitor lifecycle or IoT acceptance safe.

## Family identity at registration

The v12 registry stored device and generation but not family. The candidate
attach path already sees `priv_flags` (`INT_MAIN`, `INT_MBSSID`, `INT_APCLI`,
`INT_WDS`, `INT_MONITOR`). Host model now records that family at attach and
rejects unknown flags. `wr_iot_aux_open_reserve` requires an exact AP-client,
WDS or monitor family match before issuing a ticket. Strict C11 registration,
registry and claimed-open fixtures passed, including family mismatch and
unknown-flag refusal. This closes only the pre-dispatch identity gap in the
model: the v12 copied driver still has its old registry/dispatcher and is not
safe to package. A future claimed dispatcher must recheck the family under
the adapter lock immediately before changing `VirtualIfCnt`.

The host dispatcher predicate `wr_iot_virtual_aux_open_claim_matches` now
checks family, main-device exclusion, `AUX_START` at zero count,
`AUX_OPEN` at nonzero/nonoverflow count, current ticket and reset intent.
Its strict C11 fixture passed for valid and rejected claims. It does not
increment the vendor count itself. The v12 copied dispatcher is unchanged.

Direct source review of `rt28xx_open` found first-open work before its
failure return: profile load, IRQ request/init and `rt28xx_init`; its error
labels release IRQ when reached, but do not prove all radio/MBSS state has
returned to its pre-open state. Therefore a new `AUX_START` dispatcher branch
must not treat a failed physical open plus count decrement as a complete
rollback. Keep the claimed record/pin and route this outcome to the shared
checked recovery owner before production binding.

## Claimed auxiliary dispatcher increment (isolated candidate)

Updated `prepare-virtual-open-claim-candidate.py` so its claimed virtual-UP
branch admits `AUX_OPEN` only when the exact registered auxiliary family,
ticket, published record, adapter main device exclusion and nonzero vendor
count pass under the transition lock. `AUX_START` is still refused because
first-open failure recovery is unresolved. The generated isolated tree is
`.iot-local-check/virtual-open-claim-v14-20261025`; the production overlay
and actual AP-client/WDS/monitor wrappers were not changed.

`prepare-virtual-open-dispatch-check.py` extracted this exact branch from the
generated `cmm_cfg.c`. Its C11 fixture compiled with `-Wall -Wextra -Werror`
and passed MBSS and AP-client claimed increments plus replay rejection. This
proves the extracted branch behavior on a host model only. It does not prove
target compilation, all family wrappers, physical first-open recovery or
on-device IoT operation.

## Combined isolated source tree

`prepare-combined-open-dispatch-candidate.py` copied the reviewed v12 main
owner tree, retained its START/MAIN_OPEN branch byte-for-byte and added the
MBSS/AUX_OPEN admission branch from v14. It also overlaid the current
family-tagged registry, reference and registration fragments needed by the
auxiliary predicate. The output is `.iot-local-check/combined-open-v16-20261025`.

The exact MBSS/AUX_OPEN branch extracted from v16 compiled with strict C11
warnings and passed. `check-virtual-if-call-coverage.py` found all five source
caller families and five checked netdev attach paths. These checks do not
establish that the entire driver compiles for MIPS or that auxiliary wrappers
carry claims. In particular, legacy AP-client/WDS/monitor wrappers and DOWN
remain unowned; AUX_START and physical failure recovery remain unresolved.

## WDS non-first open owner (isolated candidate)

`prepare-wds-open-owner-candidate.py` replaced only the WDS open wrapper in
`.iot-local-check/wds-open-v17-20261025`, pinned to the reviewed v16 WDS
source. With a nonzero shared virtual-interface count, it reserves an exact
WDS record and AUX_OPEN ticket under the transition lock, passes the claim to
the common dispatcher, then retains the module pin and uncertain record after
an attempted open that cannot be proven successful. HNAT registration and TX
queue start occur only after the owned result. Zero-count WDS admission is
refused until AUX_START physical recovery is implemented.

The five-family source/registration coverage gate passed for both v16 and v17;
Python syntax checks passed. This gate checks source structure, not target C
compilation. The WDS close wrapper still uses legacy unowned DOWN, and its
failure recovery is not bound. Do not package v17 as a complete driver.

## AP-client non-first open owner (isolated candidate)

`prepare-apcli-open-owner-candidate.py` produced
`.iot-local-check/apcli-open-v18-20261025` from the pinned v17 source. The
wrapper now reserves an AP-client AUX_OPEN claim only when an existing
physical owner is present, passes the exact ticket to virtual-UP and checks
the return from `CMD_RTPRIV_IOCTL_APC_OPEN`. A failed or stale completion
retains its module pin and uncertain record for checked recovery; HNAT and
carrier actions follow only an owned result. This prevents the old wrapper
from reporting success after `ApCli_Open` returned failure.

The five-family source coverage gate passed on v17 and v18, and Python syntax
checks passed. No target compilation or real AP-client activation occurred.
The existing AP-client close path and uncertain-open recovery remain unbound;
zero-count AUX_START remains refused. v18 is not a flashable driver.

## Monitor non-first open owner (isolated candidate)

`prepare-monitor-open-owner-candidate.py` produced
`.iot-local-check/monitor-open-v19-20261025`. It reserves an exact monitor
AUX_OPEN ticket, checks virtual-UP and `SNIFF_OPEN`, and retains the module
pin/uncertain record after attempted failure. HNAT registration follows only
owned success. The monitor identity fix is included: a mismatched netdev now
returns FALSE, rather than the vendor source's unconditional TRUE. Its patched
source hash exactly matches the earlier independently tested monitor identity
candidate (`CF54CCDD...B5F784A`); that extracted C11 fixture passed.

Five-family source/registration coverage passed on v18 and v19, and Python
syntax checks passed. This is not a target compile or runtime acceptance.
Monitor close and uncertain-open recovery remain legacy/unbound; physical
first-open still needs a checked owner. Do not package v19 yet.

## Late success invalidated by reset/close/suspend

Review found that `wr_iot_radio_finish` can return success while the radio
remains UNVERIFIED or CLOSING because another actor requested reset, close or
suspend during vendor open. The v17-v19 wrappers used that return value alone
to publish an OWNED record. They are superseded by the v23 WDS, v24 AP-client
and v25 monitor isolated trees. All three now call one shared
`wr_iot_aux_open_accepted` predicate under the transition lock after ticket
retirement; it requires the same epoch/serial, READY phase and absence of
pending reset, retirement, main inhibition and PCI suspend. An invalidated
vendor success keeps UNCERTAIN_OPEN and the module pin for recovery.

The strict C11 radio-transition fixture passed normal AUX_OPEN and rejected
late success after reset or close. Python syntax and the five-family source
coverage gate passed on v25. There is no MIPS compiler on this Windows host;
the repository's optional Linux CI stage has a pinned MIPS toolchain, but v25
has not been fed to that stage or compiled. No firmware image or router state
was changed.

## Main ra0 late-success guard

The v12 main wrapper had the same late-success publication gap: it accepted
the boolean return of `wr_iot_radio_finish_unverified` even if close, reset or
PCI suspend had invalidated its ticket. Added `wr_iot_main_open_accepted` to
the shared transition model. It accepts the expected UNVERIFIED post-open
state only when the same epoch and retired serial remain current and no
invalidation is pending. The wrapper retains an UNCERTAIN_OPEN record and its
module pin if that check fails, since vendor hardware may already be open.

Strict C11 tests passed normal main START completion and rejected late
success after reset or close. Regenerated the isolated lineage: main v26,
combined dispatcher v27, WDS v28, AP-client v29 and monitor v30. The
five-family source/registration gate and Python syntax checks passed on v30.
This remains source/model evidence only; no MIPS compile, production binding
or device action occurred.

## Extracted auxiliary wrapper execution

`prepare-aux-open-wrapper-check.py` extracted the actual WDS, AP-client and
monitor `ndo_open` function bodies from the v30 isolated source into one host
C fixture. It compiled with `gcc -std=c11 -Wall -Wextra -Werror` and passed
for each family: successful claimed open, virtual-UP refusal, and a reset
arriving after the virtual-UP increment. AP-client and monitor additionally
passed failed family OPEN. Failure paths retained the pin/uncertain record
and did not register HNAT; successful paths acquired the record. The fixture
uses host stand-ins for vendor and kernel calls, so it validates these
extracted wrapper decisions, not the full MIPS driver or live radio.
