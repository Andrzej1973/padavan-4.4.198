# WR1200JS restart integration parity gate

Audited 2026-11-14 against SDK c25283e915a2a00a763774dd255b14aff997285e.
Input: preserved exact Git tar, `trunk/user/rc/net_wifi.c`, SHA256
`98bbe9cfca0af35be4ddb82742022b90cc51c2f7b34834e627ee6c5f2187dc69`.
Candidate code: d7fdc49. Source inspection only; no router operations.

The new private physical/resume path must preserve stock restart behavior before
replacing `restart_wifi_rt`. Existing source compilation does not prove parity.

| Stock operation | Current private path | Required integration |
|---|---|---|
| `stop_8021x_rt()` before DOWN | Missing orchestration | Guarded one-attempt stop before AUX/Main; uncertain result retained |
| APCLI/WDS/Guest/Main DOWN | Private fixed AUX slots and Main session | Bind request once; never invoke stock combined stop afterward |
| `gen_ralink_config_2g(0)` conditional on reload | Owned generation always runs | Honor captured reload intent, or explicitly prove required generation preserves no-reload semantics |
| `reload_svc_rt=1` when reload | Missing | Set only for corresponding captured reload; do not repeat generation |
| `mlme_state_rt(radio_on)` | Missing | Preserve `mlme_radio_rt` policy; distinguish NVRAM from driver readiness |
| Main/Guest UP and br0 attachment | Controllers implemented | Use existing exact generation/Main/Guest checks |
| `wif_control_m2u(0, Main/Guest)` | Missing | Preserve per-BSS multicast conversion after attachment; read saved `IgmpSnEnable` under ownership |
| WDS/APCLI startup | Mode0 only candidate | Preserve mode0 bridge removal; do not claim modes1–4 support from mode0 checks |
| `start_8021x_rt()` | Conditional daemon/RSSI submission | Confirm exact stock branch semantics and stop/start pair; process name alone is not ownership/readiness |
| `restart_guest_lan_isolation()` | Guest router-mode sysfs path implemented | Preserve unrelated 5GHz Guest effects without replaying global side effects |
| `check_apcli_wan(0, radio_on)` | Missing | Verify mode0 no-op or preserve exact side effects |
| `update_vga_clamp_rt(0)` | Missing | Check board macro path; preserve if compiled |
| LED_SW2G ON/OFF | Missing | Preserve terminal ordering; LED is not readiness proof |
| `/usr/bin/iappd.sh restart` | Missing | One owned terminal attempt; command return not daemon readiness |

`wif_control_m2u` calls `brport_set_m2u` with saved `IgmpSnEnable` only when
`USE_IGMP_SNOOP` is absent. Do not add a global driver setting as a substitute.
`mlme_state_rt` writes `mlme_radio_rt`; it is not an RF/DMA observation.

Keep stock entrypoints unbound until these gaps have implementation and focused
composition coverage, followed by exact MIPS/image verification. Preserve the
ACK/stale-response mechanism. Ordinary ra2 toggles must continue to avoid physical
restart/scan. Device acceptance remains a separate owner-authorized stage.


## Authentication-stop controller candidate

`restart-auth-stop.[ch]` implements SDK timing without sleeping: TERM once,
three-second observation, KILL once, one-second observation. Missing/uncertain
submission or expiry retains the owner; no retry storm or physical DOWN follows.
A stopped process is re-observed before readiness. Backward monotonic time and
pending admission refuse progress. Process-name absence is only administrative
stop evidence. Host ASan/UBSan test passes with service adapters injected.
This new module is not yet linked into preparation or physical begin. Actual
fixed-service adapters/guard and integration tests are the next step. Existing
full-suite22508 continues on unchanged d7fdc49 inputs and does not cover this new
unregistered controller. No target or device acceptance claim.

The pinned `common_ex.c::kill_services` always permits at least one second of
waiting, loops with sleep(1), and may sleep after SIGKILL. Calling it from the
RC progress tick would defeat nonblocking operation. `check_apcli_wan` can call
full_restart_wan on MAN/WISP mismatch regardless of mode0; preserve this side
effect under explicit ownership instead of assuming it is inert.
