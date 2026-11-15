# Radio ON with IoT OFF: implementation and acceptance gates

Scope: preserve configured Main/Guest while restoring the physical 2.4 GHz
radio with the pre-reserved ra2 still disabled. This is different from normal
IoT toggling, which must not restart the physical radio. MCU ACK protection,
shared DMA ownership and radio timing remain unchanged.

## Implemented private call chain

`radio-on-owner` accepts an explicit disabled intent without request credentials
or subnet. Existing retained physical RELEASE admission owns the captured
profile. `radio-on-generation` selects the saved-OFF profile scanner; reload
is attempted at most once. `radio-on-main`, Guest, multicast and services reach
PREPARED. `radio-on-disabled` captures fresh never-opened idle evidence matching
the new Main epoch and original device generation. It does not fabricate an
OPEN token or ACTIVE result.

RC compares its actual retained OFF receipt before releasing the parent.
Exact observer/context and owner survive failed signal-mask restoration.
Each disabled retry rechecks the complete profile/parent/idle/policy proof.
Cleanup wipes the saved baseline and request credentials, consumes the old
receipt once and releases the guard. Root exclusion remains through WAN/LED/
IAPP. Fresh idle and parent/profile observations gate DONE and root retirement.

Pending shutdown before Main UP follows the existing guarded rollback path.
After Main UP, prehandoff cancellation requires current profile/Main, Guest
DOWN and two fresh idle observations with matching epoch/generation and an
increasing observation serial. An exact failed disabled release can yield to
that checked shutdown owner. The generated current profile is preserved;
stock signal handling performs physical shutdown after root cleanup.

## Evidence boundaries

| Requirement | Current evidence | Remaining gate |
| --- | --- | --- |
| Profile OFF, reload0/1, mutation refusal | actual host scanner/generation fixtures | target compile and assembled image |
| Main/LAN, Guest, multicast, services | actual host controller composition with SDK actors | WR1200JS associations and policy |
| Disabled ra2 fresh identity | actual idle fixtures plus injected idle transport in root tests | real driver/RC paired target and device |
| Receipt/fence cleanup and unmask retry | actual RC cleanup and signal fence fixtures | target and device |
| WAN/LED/IAPP at most once | actual controller/terminal composition with child actor | target services and device |
| Root retirement after fresh DONE | actual stable-root fixture | target and device |
| Post-UP pending shutdown | real SIGTERM host fixture; stock handler represented by actor | physical shutdown acceptance |
| Public entry and cold routing | existing native never-opened path; private APIs only | explicit routing/binding implementation and verification |
| Full regression set for local package | complete registered host suite PASS on 6b042e90 | native exclusion fix focused regression afterward; target pending |
| Firmware ACK / late TxS safety | unchanged by this package | retain separate driver investigation and evidence |

This package does not establish final firmware image acceptance, safe flashing,
RF drain or physical runtime stability. The never-opened cold path must never
be labelled with a fabricated historical RELEASE token. Public physical ON/OFF
binding remains disabled pending its own source and target gates.

## Device verification after separate owner authorization

Use the exact verified image and save its SHA256/configuration before the test.
Record baseline Main/Guest associations and confirm IoT is disabled. Exercise
radio OFF/ON with reload0 and reload1; verify Main/Guest recovery, ra2 disabled,
no IoT bridge/DHCP/DNS gates and no unexpected OPEN. Check logs for ownership,
MCU errors and unexpected repeated starts. Verify ordinary IoT toggles separately
preserve Main/Guest and do not cause a radio restart or channel scan. Test reboot
persistence and supported shutdown boundaries only under the agreed device plan.
Host DONE or a successful build is insufficient to pass these device gates.

The native fallback also rejects both process-owned ON/OFF flags before guard,
entropy or idle observation. This closes the interval after parent release and
before root WAN/IAPP completion. The focused actual-backend regression checks
both refusal and restored cold admission after ownership clears.
