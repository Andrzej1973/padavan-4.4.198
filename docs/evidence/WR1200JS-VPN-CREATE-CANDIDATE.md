# Independent VPN profile create candidate

Implementation commit: `833ea98`. This adds authenticated raw POST import of
one WG/AWG client configuration to the independent profile store. Save does
not call up, alter the legacy tunnel, change routes/DNS or rewrite an existing
record. The existing manager validates configuration and requires an unused
ID. Metadata is token LF ID LF protocol LF followed by at most 16 KiB config.
Configuration travels through stdin, not process arguments; the HTTP request
buffer is wiped after handling. Errors are deliberately unconfirmed writes:
the operator must refresh the list before retrying.

Linux service run:
https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39070916624
Job `117508163532` log at 21:26:12 UTC confirms:

- HTTP list timeout regression passes, including a child that closes output
  but stays alive.
- Create-request grammar/bounds and NUL rejection pass.
- HTTP create auth/method/CSRF/ID/protocol rejection, stdin save without
  activation and request-buffer clearing pass under ASAN/UBSAN with fake manager.

Local `node tools/vpn-profiles/check-create-ui.js` additionally passes actual
page JavaScript tests for WG/AWG wire format, duplicate click suppression,
invalid values, secret-input clearing only on confirmed save, uncertain write
handling and no automatic activation/retry. This test is added to CI in the
follow-up working changes; it was not part of the run above.

These are component boundaries. The HTTP harness uses a fake manager; the
real manager/validators have separate integration tests. End-to-end HTTP with
the real manager, completed firmware image inspection, persistence across
reboot, physical browser creation and concurrent tunnel behavior remain open.
No profile was created on the user's router and its access tunnel was untouched.

## Real manager HTTP integration follow-up

Run `39072314133`, job `117512280547`, for `fb20045` records PASS for the real
HTTP handler → real manager → pinned WG/AWG validators → private store path:
independent WG/AWG records, exact exports, duplicate/invalid rejection and
unchanged existing records/runtime files, with no activation.
The run then failed an older delete assertion using substring `1\tAWG1`:
new row `11\tAWG11` also contains that substring. The assertion is corrected
to compare the complete first tab-separated ID field. The failed run is not
reported as a successful suite; the correction requires a new CI result.
