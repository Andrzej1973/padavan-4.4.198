# Band Steering stop investigation — 2026-10-17

The handoff reports requested `wr_bs_enable=1` but no daemon and an unavailable
control endpoint on physical build 396. This observation was not reproduced
in this investigation: a read-only SSH attempt to 192.168.20.1:22 timed out.
No service restart, setting change or radio operation was performed.

## Subsequent live observation after access returned

SSH succeeded after the user reported access restored. Requested enable is 1,
saved apply state is 5 (RUNNING), off_confirmed is 0 and saved observation is 1
(ACTIVE). However, pidof returned no daemon PID and the control client reported
an unavailable/invalid endpoint. The saved state is therefore stale and must
not be used as current activity proof.

Both configured and MLME radio values are 1, both AP modes are 0, WEP is 0,
both security modes are PSK/WPA mode 2/AES and both hidden flags are 0. SSID
and PSK were compared on the router and only equality booleans were returned;
both match. No SSID or secret was collected. These values do not support a
current profile mismatch, but cannot exclude a past transient setting or
schedule change. No matching event was found in the sampled syslog tail.
The router lacks `logread`; subsequent inspection used `/tmp/syslog.log`.

Follow-up: trace deferred child-exit status consumption and fresh observation
handling. A previously saved ACTIVE value cannot establish daemon liveness.

## Confirmed source behavior

In `tools/band-steering/prepare-wifi-lifecycle.py`, the generated
`wr_band_handle_wifi_restart()` computes effective enable from all of:
the persistent requested flag, both effective radio states/schedules and
`wr_band_profile_from_settings() == WR_PROFILE_COMPATIBLE`.
It deliberately applies disabled steering when these conditions fail while
retaining the user's requested flag. A successful disabled apply is not logged
with the reason; only an apply failure is logged here.

`profile-policy.c` requires matching SSID, hidden state, security mode and,
for PSK, WPA mode, cipher and key. It also rejects unavailable AP mode,
disabled radios and malformed values. Keys must never be logged to diagnose it.

The daemon loop in `loop.c` can also terminate on a requested stop, session
failure, clock failure, malformed/truncated events, receive errors including
ENOBUFS, or poll failure. Therefore a driver stop line alone cannot identify
the caller or establish which path was taken.

## Next implementation and runtime evidence

Added local candidate event diagnostics distinguishing requested-disabled,
radio-unavailable, profile-policy rejection and unexpected child exit,
without exposing SSIDs/keys or adding periodic logging. Preserve verified
OFF behavior and do not automatically restart an unexplained failed session.
Extended the existing generated Wi-Fi lifecycle fixture to cover profile
rejection, radio-off, clean/failed child exit and no duplicate exit message
without a new pending event. Python AST parsing and diff whitespace checks
passed locally. The generated C fixture has not yet been compiled/run for
this candidate; Linux CI and a new firmware build remain required.
Then observe effective radio/policy/status values and correlated logs on the
physical router when SSH returns. Until those observations exist, incompatibility
is a possible explanation, not the confirmed cause of the reported stop.
