# Modern Wi-Fi integration contract — 2026-11-10

Owner requires complete Modern pages, including settings, subpages and dialogs.
The image-verified read-only shell and Classic links are intermediate evidence.
Sol remains the sole writer; source development does not authorize router changes.

## Verified existing path

Pinned source: `c25283e915a2a00a763774dd255b14aff997285e`.

| Surface | Actual request / implementation |
|---|---|
| Main 2.4 GHz | `Advanced_Wireless2g_Content.asp:267`, POST `/start_apply.htm`, hidden iframe; `sid_list=WLANConfig11b;` at line 272 |
| Main 5 GHz | `Advanced_Wireless_Content.asp:278`, same route; `sid_list=WLANConfig11a;` at line 283 |
| Request metadata | `current_page`, `next_page`, `action_mode`, `action_script`; values set by existing page validation/apply logic |
| Persistence | `web_ex.c:update_variables_ex` (base line 1170), existing service-table/validate/apply loops |
| Shared preflight | `tools/prepare-shared-wifi.py` inserts `wr_shared_wifi_prepare` before any service loop; no independent Modern persistence store |
| Planning | `tools/shared-wifi/plan.h:wr_shared_wifi_make_plan`, `adapter.h:wr_shared_wifi_prepare/wr_shared_wifi_value` |
| 2.4 GHz restart metadata | base `variables.c:1237 rt_ssid`, `1256 rt_wpa_psk`: `EVM_RESTART_WIFI2` |
| 5 GHz restart metadata | base `variables.c:822 wl_ssid`, `835 wl_wpa_psk`: `EVM_RESTART_WIFI5` |

These references describe source behavior, not safe physical restart acceptance.
MCU/TxS/RF IoT blockers remain separate and unchanged.

## Existing invariants to preserve

- Shared enable requires all six coherent SSID/security/PSK fields, an explicit
  source band and both exact service memberships. Do not borrow missing fields
  from NVRAM implicitly: the existing adapter deliberately rejects that case.
- Shared disable snapshots both bands and preserves their current credentials;
  forged submitted credentials cannot replace that snapshot.
- Advanced-only changes preserve the shared selector and do not synchronize
  credentials. Channels, widths, schedules and guest settings stay independent.
- Invalid shared requests stop before persistence; arbitrary scripts and
  unsupported action modes cannot bypass coordinated validation.
- Preserve encoded SSID generation in the existing apply implementation.

## Next implementation slice

1. Define an authenticated public configuration projection (stored values, not
   a claim of live association). Exclude PSKs and other secrets from dashboard
   JSON. Distinguish unsupported security modes from empty settings.
2. Design explicit retain/change password intent. Blank input must never mean
   erase or silently reuse a key. Any server-side retention extension must be
   explicit, scoped, validated before writes and tested for both bands, shared
   sync, shared disable and conflicting/forged fields. Preserve rejection of
   ordinary incomplete Classic requests.
3. Build Modern forms with existing NVRAM names and backend apply path. Add
   validation, review/confirmation, credential clearing, failure/reconnect
   feedback and keyboard/mobile handling. Keep all currently supported Classic
   modes in scope; a WPA-Personal subset cannot count as the completed page.
4. Test rejected requests perform no writes; unchanged secrets and unrelated
   band/guest/advanced values remain unchanged. Test actual generated HTTP
   preflight as well as pure planners. Then require target/image checks and
   separately authorized physical acceptance.

No new write endpoint, secret-retention behavior or working Modern apply form
is implemented by this contract. Do not expose an Apply button before its full
request and response path is verified.

## Checks performed now

Strict host GCC + ASan/UBSan passed existing `check-validate.c`, `check-plan.c`
and `check-adapter.c`: UTF-8/byte bounds, both source bands, malformed/conflicting
requests, explicit disable snapshots, advanced-only preservation and unchanged
output on rejection. Binaries/cache are disposable and were removed. This is
host evidence only; optional978 targets the existing exact `7a7d620` package.
