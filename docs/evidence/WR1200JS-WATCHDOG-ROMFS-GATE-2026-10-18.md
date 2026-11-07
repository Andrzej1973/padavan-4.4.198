# WR1200JS watchdog status image gate — 2026-10-18

The Administration / Services page reports the saved `watchdog_cpu` choice and
the presence of the optional `rt_timer_wdg` module as separate observations.
Help text in EN, UK and RU clarifies that this does not establish operation of
the built-in MT7621 watchdog timer. The observer does not open `/dev/watchdog`
or claim that the timer is being serviced.

The final-ROMFS verifier checks the watchdog row, refresh control, HTTP
handler/provider markers and all watchdog help keys in `EN.dict`, `UK.dict`
and `RU.dict`. The service fixture and a mock final-ROMFS tree passed locally:

- `python tools/check-discovery-status.py --output .discovery-status-selftest`
- `python tools/verify-discovery-status-image.py .discovery-status-selftest/mock-final-romfs`
- `git diff --check -- tools/check-discovery-status.py tools/prepare-discovery-status.py tools/verify-discovery-status-image.py`

These are source and mock-image checks. The final firmware image gate must run
in CI after this change is pushed. Physical watchdog timer operation remains
unverified; the read-only device sample had `watchdog_cpu=1`, no optional
`rt_timer_wdg` module, and no readable active-state attribute for the separate
built-in watchdog.
