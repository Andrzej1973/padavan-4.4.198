# ZeroTier page localization and bounded status refresh — 2026-10-14

Executed by the executor agent (Sol) as the first concrete item of the ZeroTier
WebUI defect in `docs/PROJECT-DELIVERY-SCOPE.md` (screenshot defects section).
This is a **source change with local checks only**. It is not device
verification and not yet confirmed by a successful CI run.

## Change

New port step `overlay/padavan-4.4/ports/zerotier/localize-ui-page.py`, invoked
last by `overlay/padavan-4.4/ports/zerotier/prepare-ui-lifecycle.py` so it runs
after the steps that add the access rows, the status panel and the leave
control.

1. Every Chinese caption, list option and help text inherited from the pinned
   `Advanced_zerotier.asp` (36 items) is replaced by a dictionary key; the file
   must contain no CJK characters afterwards.
2. Help blocks written by earlier steps (status help, router access, LAN
   access, join help) and the `Unknown` status literal are replaced by keys so
   the page keeps one translation owner.
3. The `刷新页面` / `window.location.reload()` button is replaced by a
   `Refresh status` control plus a `#zerotier_state_info` freshness/error area.
4. New authenticated JSON endpoint `zerotier_state` in `web_ex.c`
   (`/update.cgi?output=zerotier_state`) returns `{"state":N,"age":S}` where
   state is `0` disabled, `1` fresh, `2` stale (cache older than 60 s), `3`
   unavailable.
5. Page JavaScript refreshes on entry and every 30 s, pauses in hidden tabs
   (`document.hidden`), guards against overlapping requests, shows
   updated/stale/unavailable/refresh-failed text and refreshes immediately when
   the tab becomes visible again.
6. 36 keys added to `trunk/user/www/dict/EN.footer`, `UK.dict` and `RU.dict`.

## Files

- `overlay/padavan-4.4/ports/zerotier/localize-ui-page.py` (new)
- `overlay/padavan-4.4/ports/zerotier/prepare-ui-lifecycle.py`
- `overlay/padavan-4.4/ports/zerotier/verify-image.py`
- `.github/workflows/build-padavan-4.4-wr1200js.yml`

## Local verification

Assembled tree: base source fixture plus the post-overlay ZeroTier page
(`zerotier-localize-check-3`). The port script applied cleanly and the local
validator reported `RESULT ALL PASS` for 24 assertions: no CJK left in the
page, the refresh controls and keys present, `window.location.reload` removed,
36 keys present and non-empty in all three dictionaries with distinct
Ukrainian/Russian values, exactly one handler definition and one registration
with balanced braces, the inserted JavaScript passes `node --check`, the
`--verify-image` mode passes, and a repeated apply refuses to duplicate keys.

`AST OK` was confirmed for all three changed Python files. The workflow YAML was
edited in the existing step style; no YAML parser is available locally, so the
structure was reviewed by hand.

## Not verified

- The new C handler is **not compiled locally**; there is no compiler in this
  environment. Compilation is covered by the WR1200JS build job.
- No device runtime check: refresh, freshness text, Apply, daemon lifecycle,
  membership preservation, permissions and real connectivity remain open.
- `CN.dict` is not translated (same choice as the existing ZRAM status labels).
- Moon and static routes are **not yet grouped** under advanced controls, and
  the legacy NAT switch is **not yet reconciled** against the access switches
  and the firewall implementation.
- Other pages still contain Chinese text: `Shadowsocks.asp`,
  `Advanced_smartdns.asp`, `Advanced_SQM.asp`, the ZeroTier menu entries and the
  `EN.footer`/`menu5_*` and `SmartDNS_*` entries.

## CI coverage

The build workflow now runs
`python3 overlay/padavan-4.4/ports/zerotier/localize-ui-page.py padavan-4.4 --verify-image`
after the ZeroTier closure step when `CONFIG_FIRMWARE_INCLUDE_ZEROTIER=y`. It
asserts the shipped page has no CJK, still contains the refresh controls, no
longer reloads the document, and that EN/UK/RU dictionaries carry the exact
expected values. `overlay/padavan-4.4/ports/zerotier/verify-image.py` now also
requires the `wrZerotierRefresh`, `zerotier_state_info` and `zerotier_state`
markers.
