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
driver status. The check does not establish why the daemon stopped, whether
clients were steered before the stop, or whether the current flashed image
matches a particular CI build. No restart was attempted.