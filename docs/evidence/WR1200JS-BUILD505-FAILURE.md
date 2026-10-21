# WR1200JS build #505 — pre-compilation VPN page gate failure

GitHub Actions run `39465298056` failed on 2026-10-20. The failing job was
`build (wr1200js) / build-wr1200js` (`118775062000`). Compilation and image
verification were skipped. This is the latest failed attempt known at the
time of writing; #504 remains the latest successful firmware image.

## Observed failure

The step `Exclude legacy VPN userspace from WR1200JS` exited 1 with:

```text
VPN protocol option changed: vpncli.asp 0
```

The same step had already completed `prepare-wg-tool-separation.py`; the error
occurred in `prepare-wr-vpn-pruning.py`. IMQ patch hunks were also rejected in
the preceding preparation stage, but the workflow continued past that stage.
Those rejects were not the fatal exit in this run.

## Root cause in the workflow sequence

The earlier `tools/vpn-profiles/prepare-web.py` transformation calls
`remove_unavailable_legacy_types()` for `vpncli.asp` and `vpnsrv.asp`, removing
PPTP/L2TP options 0 and 1. Later, `tools/prepare-wr-vpn-pruning.py` attempted
to remove options 0, 1, and 2 from the same selectors and required each to be
present exactly once. It therefore stopped at option 0 before the compiler was
downloaded or invoked. The failure is a duplicate, non-idempotent WebUI
transformation, not a C/compiler error.

## Local source correction

The VPN type helper now has an explicit prior-pruning mode. The later WR
pruning step accepts PPTP/L2TP as already removed but requires and removes
OpenVPN option 2. The existing `check-wr-vpn-pruning.py` remains the strict
final contract: client/server selectors must contain only supported value 3,
and WAN must contain only DHCP/static/PPPoE. The in-memory regression fixture
covers both client and server, compares one full transformation with the
earlier-plus-later workflow, requires only value 3, and rejects missing or
duplicate OpenVPN options.

## Verification boundary

The source-level correction and fixture are local and uncommitted. The
in-memory client/server positive and fail-closed cases, Python syntax parse,
and whitespace check have been run successfully. No full firmware build,
CI run, image inspection, router write, or runtime verification has been done
for this correction. Build #504's successful CI/image evidence remains valid
only for its recorded source head and does not include this fix.
