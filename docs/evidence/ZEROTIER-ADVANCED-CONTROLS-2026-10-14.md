# ZeroTier advanced controls grouping and legacy NAT reconciliation - 2026-10-14

Executed by the executor agent (Sol) as the second concrete item of the
ZeroTier WebUI defect in `docs/PROJECT-DELIVERY-SCOPE.md` (screenshot defects
section). This is a **source change with local checks only**. It is not device
verification and not yet confirmed by a successful CI run.

The first item (page localisation and bounded status refresh) is now confirmed
by build 271: the compiled job step `Verify ZeroTier page localization and
bounded status refresh` passed on the shipped ROMFS page
([run 38624227422, step 52](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38624227422)).

## Change

New port step `overlay/padavan-4.4/ports/zerotier/prepare-advanced-controls.py`,
invoked last by `overlay/padavan-4.4/ports/zerotier/prepare-ui-lifecycle.py`, so
it runs after the step that replaces the inherited Chinese captions with
dictionary keys.

1. The legacy NAT row, the four Moon rows and the static-routes table are marked
   with `class="zt_advanced"` (five rows plus `class="table zt_advanced"` for the
   routes table) and a toggle row is inserted above them.
2. The page script collapses that group on load. Without scripting every control
   stays visible, so the group can never hide a setting from a client whose
   scripting fails; the collapse is not persisted between page loads.
3. The single Apply control was inside the routes table. It is moved out of the
   table into its own container so it stays reachable while the group is
   collapsed. `--verify-image` asserts exactly one Apply control and that it is
   positioned after the advanced table.
4. `<th>ZeroTier Moon Network ID</th>` was hardcoded English; it now uses the new
   `ZT_MoonNetworkID` key.
5. The legacy NAT label and help text were rewritten to match the implemented
   firewall policy: masquerading applies only while `zerotier_lan_access` is on
   and `zerotier_nat` is on, only for overlay IPv4 source prefixes toward the
   LAN interface, and never toward WAN or other VPNs - exactly the condition in
   `overlay/padavan-4.4/ports/zerotier/firewall-policy.sh` (`zt_policy_nat`) and
   in the compiled guards from `prepare-firewall-hook.py`.
6. Five keys were added and two reworded in the single translation owner
   (`localize-ui-page.py`): `ZT_AdvancedHeading`, `ZT_AdvancedShow`,
   `ZT_AdvancedHide`, `ZT_AdvancedHelp`, `ZT_MoonNetworkID`, plus the updated
   `ZT_AllowNAT` and `ZT_NatHelp`.

## Files

- `overlay/padavan-4.4/ports/zerotier/prepare-advanced-controls.py` (new)
- `overlay/padavan-4.4/ports/zerotier/localize-ui-page.py`
- `overlay/padavan-4.4/ports/zerotier/prepare-ui-lifecycle.py`
- `overlay/padavan-4.4/ports/zerotier/verify-image.py`
- `.github/workflows/build-padavan-4.4-wr1200js.yml`

## Local verification

Full chain on two assembled trees (`zt-advanced-check-1`, `zt-advanced-check-2`):
pristine pinned source `webui-audit/base` plus the pinned `www/dict` files, then
`harden-zerotier-lifecycle.py` followed by `prepare-ui-lifecycle.py`. The chain
completed and printed the new step result.

- 38 assertions passed on both trees: no CJK left in the page, five grouped rows,
  one grouped routes table, toggle control present, Moon header keyed, exactly
  one Apply control and it sits after the advanced table, the inserted JavaScript
  passes `node --check`, the initialisation call is wired into `initial()`, and
  all seven keys exist exactly once per dictionary with distinct Ukrainian and
  Russian values.
- Re-running the step on the finished tree fails with a clean anchor mismatch and
  leaves the page byte-identical (sha256 compared before and after).
- `prepare-advanced-controls.py --verify-image` and
  `localize-ui-page.py --verify-image` both pass against an assembled
  `trunk/romfs/www` image.
- `ast.parse` succeeded for the four changed Python files.
- A defect found during this work is recorded in the step history: string
  literal concatenation plus `*` precedence silently produced wrong anchors and
  was fixed before the step was accepted.

## Not verified

- Nothing is compiled locally; there is no compiler in this environment. The
  build job compiles the page and the C changes that the earlier steps add.
- No device runtime check: the advanced group, the moved Apply control, the
  collapse behaviour, freshness display, permissions and connectivity remain
  open until the device is used.
- The collapse state is intentionally not persisted; this is a deliberate
  behaviour choice, not a verified user preference.

## CI coverage

The build workflow runs
`python3 overlay/padavan-4.4/ports/zerotier/prepare-advanced-controls.py padavan-4.4 --verify-image`
after the localisation step when `CONFIG_FIRMWARE_INCLUDE_ZEROTIER=y`, and
`verify-image.py` additionally requires the `zt_advanced` and
`zerotier_advanced_toggle` markers in the shipped page.