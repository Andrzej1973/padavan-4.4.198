# Direct key ioctl boundary

Focused source/host review, 2026-11-18. This is an open integration requirement,
not a device race reproduction or a completed fix.

`mcu-control-admission.inc:wr_iot_control_enter` counts live control actors and
excludes transition/reset/PM. It intentionally permits multiple actors and does
not check the ra2 key arbiter. `prepare-mcu-control-admission.py` wraps the public
`rt28xx_ioctl` using that admission. The Linux API producer keeps this wrapper
for ordinary ioctls. Therefore this outer lifetime fence alone cannot prove
that direct key writes exclude the requested/periodic GTK writer.

Pinned vendor `ap/ap_cfg.c` contains HOSTAPD_OID_SET_KEY and
HOSTAPD_OID_DEL_KEY under HOSTAPD_SUPPORT, including direct MAC lookup and
key table changes. Pinned os/linux/config.mk defaults HAS_HOSTAPD_SUPPORT=n.
Actual per-unit effective macro reports are being added to the optional build;
source defaults are not proof of final target exclusion. Other native setters
also mutate shared-key configuration and need classification by their guards
and callers before claiming complete configuration/key serialization.

`tools/iot/check-control-key-exclusion-gap.c` executes the actual counted
admission with a boundary adapter. With one active GTK key owner/reference, a
second generic control caller enters and exits without changing the key flag.
ASan/UBSan host check passes by confirming this counterexample. It does not
execute an ioctl, emulate parallel CPU execution or assert firmware behavior.

Next implementation boundary: classify reachable mutation commands before the
first native state change, bind the exact BSS/adapter and retain the same ra2
arbiter through native execution. Preserve query behavior and Main/Guest paths.
Global setters that can affect ra2 require explicit classification; netdev name
alone is insufficient. Do not hold table/transition spinlocks across user copy,
crypto, timer cancellation or hardware writes. Do not globally change counted
control admission: independent control actors and nested MCU sends depend on it.
Queued EAPOL generation validation remains a separate implemented boundary.

## Exact dispatch and cross-BSS identity follow-up

`RTMP_AP_IoctlHandle` dispatches CMD_RT_PRIV_IOCTL to RTMPAPSetInformation only
when `subcmd & OID_GET_SET_TOGGLE`; the latter switches on `cmd & 0x7FFF`.
Any new classifier must preserve this masking and distinguish GET commands.
Both HOSTAPD key cases currently call MacTableLookup with only the payload MAC.
`mgmt/mgmt_entrytb.c:MacTableLookup` compares only Addr in the hash chain.
Consequently an ioctl selected on Main/Guest cannot be assumed incapable of
finding a ra2 station. A selector-only wrapper would leave this path unproven.
The same SDK offers MacTableLookup2(ad,addr,wdev), with exact wdev comparison,
but substituting a lookup alone does not pin the entry through native key I/O.

Required implementation properties now identified: copy/validate the payload
once before classification; use the same trusted payload for execution; bind
both requested BSS and resolved peer; retain station generation and key-writer
ownership until native completion; balance every early return. Existing native
copy_from_user status/length handling must be reviewed during factoring. Do not
introduce a second user copy as a supposedly immutable authorization snapshot.
These are source-derived requirements, not an implemented ioctl correction.

## Input-copy correction in isolated candidate

The Linux API producer now applies hostapd-key-copy-composition.py to ap_cfg.c.
Both HOSTAPD SET_KEY/DEL_KEY cases return -EFAULT through the native switch exit
when copy_from_user reports uncopied bytes, before MacTableLookup or mutation.
Successful requests retain the native single copy and native processing.
The transform rejects missing/duplicate anchors and repeated installation.
check-hostapd-key-copy.py executes the native input preludes with explicit
payload/copy/lookup boundary actors under ASan/UBSan; null pointer, malformed
length, partial-copy refusal and success pass for both commands. This is not a
full HOSTAPD feature compilation or ioctl lifetime fix. Actual target feature
flags, BSS/generation retention for successful writes and runtime remain open.
The source snapshot now includes ap_cfg.c for independent review.

## Lookup availability correction

The vendor MacTableLookup2 definition and declaration are guarded by
WH_EZ_SETUP. Optional1406 actual AP startup macro evidence has WH_EZ_SETUP
disabled. This function must not be called unconditionally by the new ioctl
code. Enabling Easy Setup solely to obtain a lookup is also inappropriate.
A localized exact-BSS lookup using the existing hash/entry structures, under
MacTabLock with explicit generation/lifetime reservation, is required unless
the target-specific feature evidence establishes another suitable existing API.
This corrects the earlier lookup suggestion; the ioctl lifetime gap stays open.

## Prepared retained ra2 peer lookup

ra2-direct-key-peer.h provides wr_ra2_direct_key_peer_locked using the existing
MacTab.Content array; it has no WH_EZ_SETUP dependency. The caller must already
hold MacTabLock, the exclusive ra2 key arbiter and a successful retained-peer
scope through the eventual key operation. It validates exact ra2 wdev/type/index,
WCID, retained generation and reservation before returning a pointer. Foreign-only
MAC matches, duplicate ra2 MAC entries and inconsistent generations fail closed.
No match is a distinct result and does not authorize group-key fallback.
check-ra2-direct-key-peer.py executes the helper with existing retained-peer
admission under ASan/UBSan in direct and OS_ABL lock forms. It covers a same-MAC
Guest entry alongside ra2, absence, generation drift, foreign-only lookup and
duplicate ra2 entries. This helper is not yet installed or bound to ioctl native
execution; successful-request lifetime and target verification remain open.

## Prepared direct-key synchronous lifetime scope

ra2-direct-key-scope.h composes existing OPEN/control admission, the shared
exclusive key ticket and retained ra2 peer generations. It is a private linear
stack scope, not a firmware token. Admission rolls back its own control/key
reservation if peer admission fails. Release validates adapter/key ownership
before touching peer reservations; foreign release poisons only the supplied
adapter and retains the original owner's scope. Generation drift preserves
foreign peer reservations and poisons subsequent admission. No lock is held
across eventual user copy, native key I/O or crypto. The caller already pins
adapter lifetime.

check-ra2-direct-key-scope.py passes direct/OS_ABL ASan/UBSan host checks for
successful release, reentry refusal, reassociation/deletion exclusion, older
table transaction rollback, active association refusal, foreign-adapter leave
and generation-drift cleanup. The fixture executes the actual helper contracts
with SDK boundary actors; it does not run HOSTAPD key I/O or firmware. Neither
new helper is installed in production or the isolated producer yet. Next step
is factoring trusted SET/DEL payload execution and binding this scope around
all native exit paths without a second copy_from_user.

## Prepared trusted-payload native execution factoring

hostapd-key-execution-composition.py extracts the native SET/DEL mutation bodies
into HOSTAPD-guarded functions taking an already copied payload, selected BSS
and previously resolved entry. Neither helper copies user memory or performs a
new MAC lookup. The SET branch's original captured apidx is passed unchanged;
its now-unused local KeyIdx declaration is removed. All native mutation body
bytes remain unchanged. The call-site copy rejection remains mandatory.
check-hostapd-key-execution-composition.py reconstructs the exact input source
from replacement receipts, verifies one copy for each payload and refuses
missing copy guards or duplicate application. This is source transformation
verification only: generated helpers have not been target-compiled or executed,
are not installed by the producer, and still require scoped ioctl dispatch.
Native group-delete payload semantics and bounds of successful key material
must be resolved before activating the complete successful-request path.

## Native mutation body host execution

check-hostapd-key-native.py now compiles the factored native bodies and executes
AES pairwise/group insertion, pairwise removal and WCID-zero refusal under
ASan/UBSan. Payload and CIPHER_KEY definitions are extracted verbatim from the
pinned SDK; adapter/entry boundary structs expose the fields used by those
bodies, and hardware calls are explicit counting actors. Compiler warning
suppression is limited to the inherited DEL comparison of an embedded address
array to NULL, which cannot establish group-delete intent. Successful payload
bounds, TKIP/MIC protocol semantics, complete feature compilation and physical
key I/O remain unverified. No ioctl ownership binding is claimed by these tests.

## Correction: host fixture BSS layout and dormant HOSTAPD code

The original native-body host fixture supplied direct BSS DefaultKeyId and
GroupKeyWepStatus fields for the legacy source references. Actual rtmp.h defines
these in embedded wifi_dev, not BSS_STRUCT. Therefore the earlier host success
proved body execution on that boundary model, not compatibility with the actual
SDK BSS layout. It must not be cited as HOSTAPD feature compilation evidence.

The corrected fixture validates those source declarations, omits the invented
direct fields and requires the unchanged native helper compilation to fail on
them. A separate uninstalled hostapd-key-layout-composition.py rewrites only the
25 exact helper field references to wdev. The corrected helpers then compile
and execute the AES/pair-delete cases under ASan/UBSan. Other HOSTAPD source
branches have not been ported or target-built. This is a dormant optional-path
compatibility preparation, not an IoT blocker resolution or enabled feature.

## Actual target feature evidence — optional1418, 2026-11-19

Run44387982878/artifact14470698228 for c6544dd5 contains complete Kbuild-command
preprocessing reports for ap_cfg.c, ap_wpa.c and cmm_wpa.c. All three report
HOSTAPD_SUPPORT=false and WH_EZ_SETUP=false. HOSTAPD SET_KEY/DEL_KEY cases are
therefore excluded in this exact candidate configuration. The unbound direct
key preparation is not required to claim coverage of an excluded branch and
must not cause that dormant feature to be enabled. APCLI_SUPPORT,
MAC_REPEATER_SUPPORT,DOT1X_SUPPORT,DOT11R_FT_SUPPORT are true in all three TUs;
those active paths retain their own lifetime/association review requirements.
Module and prepared-source hashes were independently verified, with actual
selected TRX contents checked separately. See OPTIONAL1418-KEY-FEATURE-AUDIT
and OPTIONAL1418-SELECTED-IMAGE-AUDIT evidence dated2026-11-19. These results
exclude later stale-retirement/MAC-ambiguity fixes and physical runtime.
