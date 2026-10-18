# Band Steering runtime check — 2026-10-18

Read-only SSH inspection of the physical WR1200JS. No service, radio, setting,
or router state was changed.

## Observed state

| Check | Observation | Meaning |
| --- | --- | --- |
| Requested setting | wr_bs_enable=1 | User setting requests enable; does not prove operation. |
| Package files | /usr/sbin/wr-band-steering and /usr/sbin/wr-band-steering-ctl are executable | Daemon and status client are installed. |
| rc integration marker | /sbin/rc contains a reference to /usr/sbin/wr-band-steering | Startup/lifecycle code is present in the running rc binary; this alone does not prove it started successfully. |
| Daemon | No matching process name in /proc | Daemon is not running at the observation time. |
| Control endpoint | /var/run/wr-band-steering/control is absent | No live local status endpoint. |
| Direct status | Client reports “Control endpoint unavailable or invalid; radio state unverified.” | Driver/radio steering state is explicitly unverified. |
| Cached state | wr_bs_apply_state=5, wr_bs_off_confirmed=0, wr_bs_observation=1 | Stored RUNNING/ACTIVE indication is stale without a live daemon and fresh observation. |
| Retained kernel log | Start marker at Oct 17 12:48:42; stop marker at Oct 17 16:01:40 | Steering started then stopped; no later start marker appeared in the sampled retained log. |
| Other log context | No direct service exit reason was established from the sampled records | Cause of stop remains unknown. |

## Conclusion and limits

Band Steering is not verified as operating now. The requested flag and cached
RUNNING/ACTIVE values cannot override the missing process/socket and the direct
status response. The log proves a historical start/stop pair, not current
driver status. The installed image is confirmed as build 396
(`4.4.198.9-396_82233894`): the user confirmed that this is the image flashed
on 2026-10-17, the device's kernel build fingerprint matches its installation
record, and the original acceptance record contains the verified image hash.
The check does not establish why the daemon stopped or whether clients were
steered before the stop. No restart was attempted.

## Later candidate CI evidence

The diagnostic source change in commit `347be00` is an ancestor of the full
build #457 source commit `4cd56a8`. GitHub Actions run `39116103457` reports
the "Prepare requested WR Band Steering integration" step and the full
"Build WR1200JS firmware" step as successful. Separate Band Steering ABI run
`39115399202` also passed "Verify actual rc Wi-Fi lifecycle callbacks".
These are source/compile and mocked-callback results; neither is runtime
evidence for the installed build #396. The full-build ROMFS checks verify the
daemon, control client and rc integration marker, but do not explicitly assert
that the new diagnostic strings are present in final `romfs/sbin/rc`; exact
diagnostic presence in #457 therefore remains unverified. No newer image was
flashed.

After reviewing that gap, the main firmware workflow was locally updated to
require five final-ROMFS `sbin/rc` diagnostic markers: owned child exit,
disabled apply reason, apply failure, boot profile write failure and shutdown
OFF acknowledgement failure. A source-to-gate check and `git diff --check`
passed. This gate was added after #457 and has not yet run in GitHub Actions;
it is not evidence that the markers are present in #457 or in the installed
build #396.
