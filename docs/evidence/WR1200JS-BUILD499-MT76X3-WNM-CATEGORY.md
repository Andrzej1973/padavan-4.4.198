# WR1200JS build #499: MT76x3 WNM category guard

- Workflow run: `39454755757` ([GitHub Actions](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39454755757))
- Built revision: `e0880713a48a1b8204b2c1b81df7c94bc928fb30`
- Result: failed during MT7603 kernel module compilation.
- Job: `build (wr1200js) / build-wr1200js` (`118738627471`), 2026-10-20 16:08:22–16:10:50 UTC.

## Observed failure

The compiler stopped at `drivers/net/wireless/mediatek/mt76x3/common/action.c:106`:

```text
error: 'CATEGORY_WNM' undeclared (first use in this function)
StateMachineSetAction(S, ACT_IDLE, CATEGORY_WNM, (STATE_MACHINE_FUNC)PeerWNMAction);
```

The selected MT76x3 build enables `CONFIG_DOT11V_WNM`, which compiles the WNM action handler, while `CATEGORY_WNM` in `mt76x3/include/rtmp_def.h` was nested under `DOT11W_PMF_SUPPORT`. PMF is independently disabled in this build, leaving the WNM handler without its category constant. This is a source-level guard mismatch, not a reason to enable PMF or change the board configuration.

## Change

`tools/prepare-mt7603-wnm-category.py` moves only `CATEGORY_WNM` under its own `CONFIG_DOT11V_WNM` guard and keeps PMF categories under `DOT11W_PMF_SUPPORT`. The WR1200JS workflow applies this narrow source transform after fetching the pinned source and before compiling.

## Checks and limits

- Matched the transform against the pinned local MT76x3 header; the transform was idempotent.
- Compiled a small C preprocessor/compiler fixture with GCC across all four WNM/PMF enabled/disabled combinations: 4/4 passed. `CATEGORY_WNM` exists exactly when WNM is enabled.
- `git diff --check` passed for the changed script and workflow.
- No full firmware compile was run locally. The next GitHub Actions build is required to confirm the module and image build.
- This CI result does not demonstrate runtime Wi-Fi feature acceptance on the router.

## Log identity

The downloaded run log examined locally had SHA-256 `DDC037430C4ED9F6A9CA005CC632DEEB0394A8273A51420CE435514A51BDEC3A`.
