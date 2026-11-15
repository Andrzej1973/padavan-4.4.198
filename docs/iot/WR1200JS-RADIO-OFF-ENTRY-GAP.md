# Physical radio OFF entry integration gap — 2026-11-15

Scope: source audit of 6c786921; no device action or acceptance.

The existing private restart entry accepts radio_on=1 only. Extending it to
radio_on=0 is not a one-line predicate change.

| Boundary | Current source | Required work |
| --- | --- | --- |
| Intent | restart-entry.c initializes {restart=1,radio_on=1,reload} | Define OFF intent and SDK side effects separately from ON resume |
| Physical progress | rc-physical-stop.c stops polling after result is published | Install an explicit process-owned terminal consumer; otherwise owner remains allocated |
| Consumption | wr_iot_rc_physical_take clears the retained context exactly once | Consume only the matching private OFF transaction, never another caller's result |
| Scheduler | restart-scheduler.c requires restart && radio_on | OFF cannot be handed to the existing ON scheduler |
| Signal replay | non-restart physical_step ends fence before assigning physical.result | Before enabling OFF entry, test pending shutdown and prove cleanup/publication ordering; do not infer it from ON resume cleanup |
| Legacy fallback | prepare-rc.py calls wr_iot_quiesce before stop_8021x/profile generation; rc-backend.c refuses ACTIVE/STOP/OFF | Preserve refusal and isolation; a failed private entry must not bypass it |

Implementation acceptance: a private OFF owner with exact intent correlation;
nonblocking completion through RC wait; one terminal take; no ON scheduler,
profile regeneration or accidental reopen; pending SIGTERM/SIGQUIT, failed mask
restore, repeated OFF, new ON after completed OFF, and foreign-result refusal.
Existing saved configuration must survive. Inspect the pinned SDK OFF branch
for required LED/auth/IAPP/WAN behavior before selecting those side effects.

The current full host suite remains separate evidence. Its success cannot
prove this not-yet-bound OFF entry. The radio_on=0 refusal remains in place.

## Pinned SDK OFF behavior confirmed

Inspected trunk/user/rc/net_wifi.c directly in the retained exact c25283e
archive without extraction. restart_wifi_rt(0,reload) calls stop_8021x_rt,
stop_wifi_all_rt; reload additionally generates the profile and sets temporary
reload_svc_rt=1. start_wifi_ap_rt(0) detaches Main/Guest from br0 and calls
mlme_state_rt(0). start_wifi_wds_rt(0) detaches all four WDS interfaces;
start_wifi_apcli_rt(0) detaches APCLI. No interface-UP branch is selected.
The subsequent auth starter, Guest isolation and IAPP restart remain calls
whose OFF-specific behavior must be traced before replacing them.

check_apcli_wan(0,0) skips AP mode; in router mode it still invokes
full_restart_wan when MAN and configured WISP bands differ. It does not
invoke try_wan_reconnect for radio OFF. Therefore physical descriptor drain
alone does not preserve the SDK OFF network/configuration semantics.

ABI43667886374 completed success for6c786921. Local full-suite session62243
and its log disappeared before terminal observation: local full result is
UNVERIFIED, not PASS. Do not infer its exit status from absence.
