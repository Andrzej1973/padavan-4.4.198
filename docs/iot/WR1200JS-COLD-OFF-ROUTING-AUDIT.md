# Cold/IoT-OFF and concurrent physical admission audit

The never-opened ra2 path differs from an owned CLOSED ra2:

- `initial-off.c:wr_iot_initial_off_begin/observed` uses fresh idle epoch,
  generation and increasing observation serial, no OPEN token or CLOSE serial.
- `prepare-restart-entry-source.py` keeps IDLE/INITIAL_OFF on the separately
  guarded legacy SDK path. Claimed owned restart returns before that path.
- `rc-backend.c:wr_iot_activation_prepare_radio_stop` admits only fresh
  never-opened evidence there. Missing bridge/empty config alone is insufficient.
- `quiesce_begin` admits actual ACTIVE/OFF backend owners, not INITIAL_OFF.
  Physical STOP protocol requires nonzero OPEN/CLOSE provenance, so never-opened
  idle evidence cannot be converted into that RELEASE tuple.
- Private ON root now supports enabled0 and enabled1 after a historical physical
  RELEASE. Disabled restoration/release/followup/root/shutdown have host coverage.
  Public physical OFF/ON binding remains disabled pending separate routing and
  target gates. Never-opened cold evidence is still not a RELEASE tuple.

The audit found a concurrent-admission hole: after ON parent release, signal
admission is inactive but the root still owns WAN/IAPP. Direct physical_begin
and restart_entry checked active/pending only. Both now refuse process-owned
ON/OFF exclusion before scheduler preparation, mode reads, fences or driver
work. This keeps the normal never-opened path available when no owner exists.
Focused actual physical/session/fence fixture verifies both flags cause zero
scheduler/guard/driver calls; entry fixture checks zero mode/guard/submission.
Normal OFF composition, ON shutdown, prepared entry and separate units pass.
Host checks use backend/SDK transports; target/device claims remain separate.

Next: define typed never-opened physical stop/resume provenance or explicitly
validated cold SDK routing, and a saved-IoT-OFF Main/Guest restoration path.
Do not invent OPEN token/close serial, convert idle to CLOSED, or globally loosen
physical admission. Keep ordinary precreated ra2 runtime toggle independent.

## Rechecked evidence boundaries

`check-initial-off-composition.py` and `check-initial-off-owner-composition.py`
were rerun against current source: the existing never-opened initial-OFF
observation/owner path passes host composition. This does not add a physical
OFF/ON lifecycle for desired IoT OFF.

Optional1257/43691352008 artifact14155452722 was independently inspected. Its
verification-source artifact identifies verified28229bf1 versus dispatch68a3e7f1.
Target result matches verified28229bf1 and reports compiled peer82 MT7603 module
SHA256 e2675b461ebb8712b1cff86892aac0ac55c757ce63581c1ad78ba976211bab64.
Actual RC/HTTPD ELF headers are MIPS32r2 and both dependency-closure reports pass
with no errors. The reports explicitly retain production_installed=false and
runtime_verified=false. This verifies that older candidate, not subsequent ON
root/shutdown patches or final image inclusion. Full JSON/hash evidence is kept
in WR1200JS-OPTIONAL1257-TARGET-LINK-2026-11-15.json. Archives were inspected in
memory; no extracted firmware/build tree was retained.

## Pinned SDK restart call chain verified

Inspected exact c25283e915a2a00a763774dd255b14aff997285e archive,
`trunk/user/rc/net_wifi.c`: stop_wifi_all_rt:404, start_wifi_ap_rt:461,
start_wifi_wds_rt:557, start_wifi_apcli_rt:637, restart_wifi_rt:764.
The stop helper stops APCLI, four WDS interfaces, Guest and Main; no ra2 appears.
The restart helper stops authentication/radio, optionally generates config,
then starts AP/WDS/APCLI, authentication, isolation, WAN, LED and IAPP.
Mode0 WDS/APCLI start helpers only detach their bridge memberships.
Main/Guest start sets MLME state then UP/bridge/multicast under saved policy.

Consequently a never-opened ra2 proof is essential before the native fallback;
that stop list does not independently certify an owned ra2 closure. Desired IoT
OFF after a prior physical RELEASE needs a distinct disabled-ra2 completion
with fresh new-adapter epoch/generation and idle observation, Main/Guest/network
proof and terminal cleanup. Do not synthesize an OPEN nonce/CLOSE serial for
this branch or send a dummy OPEN simply to reuse enabled1 handoff. This remains
an implementation requirement; source call-chain evidence is not runtime proof.
Exact function extracts are in COLD-OFF-SDK-CALLCHAIN evidence.

## Restarted idle relationship primitive

`initial-off.c:wr_iot_initial_off_restarted_observed` checks fresh never-opened
idle against a supplied valid old RELEASE and supplied new Main identity.
New Main epoch must strictly exceed the released epoch, device generation must
match, and fresh idle must match new Main exactly. Pending shutdown refuses.
Caller still has to own/revalidate actual RELEASE and Main: this helper cannot
turn supplied structs into authority. It neither opens ra2 nor retires resources.
Actual initial-OFF/owner composition tests pass, including relationship drift
and unchanged inputs. Physical ON root integration and IoT-OFF completion remain
open; no device or target acceptance inferred.

`restart-profile.c:wr_iot_restart_disabled_profile_current` provides an explicit
saved-OFF check with the existing strict third-BSS scanner and double file
readback. Saved ON refuses before file capture; saved enable drift between
reads refuses. The original ON-request scanner retains its semantics. Temporary
credentials are wiped, no profile/NVRAM generation/write is performed. This
primitive and restarted-idle observation still require composition into the
Main/Guest restoration and terminal ownership path before IoT OFF is complete.

## Disabled-profile restore through PREPARED

Generation now accepts explicit enabled0 with empty request SSID/password,
selecting the strict saved-OFF scanner. Main checks this selected policy rather
than assuming enabled1. Actual restore composition reaches PREPARED with Main/
LAN, Guest, multicast and services under enabled0; reload0/1, Guest OFF and
failure-retention fixtures pass. No ra2 OPEN occurs in this composition.
Public root and normal handoff remain enabled1-only. PREPARED for enabled0
requires a distinct fresh idle/parent completion and checked receipt/fence/root
retirement; it cannot use enabled1 rebind ACTIVE proof or signal ON success.

`radio-on-disabled.c` now retains a stable borrowed PREPARED parent and an
initial-OFF idle witness. It checks exact child links, enabled0, no handoff or
WAN/terminal child, fresh parent state before/after restarted idle observation.
Duplicate begin refuses; loss of idle or Main identity holds ownership. This
observer is staged and compiled separately, but does not authorize retirement
or bind the public root. Actual restore composition with injected idle transport
passes; actual idle implementation has separate source/composition coverage.

## Current package status

The staged progression above records the order of implementation; statements
about still-missing private root/shutdown describe those intermediate stages.
The current private disabled root now reaches fresh DONE and handles pre-release
post-UP shutdown. Full registered host suite passed on 6b042e90. The subsequently
applied native process-exclusion fix passed focused backend/root/prepared checks.
Public binding, target/image and physical acceptance remain open; the acceptance
matrix is the current gate list.
