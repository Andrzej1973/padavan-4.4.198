# Local browser verification of the Wi-Fi monitor

The current production JavaScript assets were loaded in a local browser fixture with synthetic observations. This does not verify router runtime or driver behavior.

Verified on 2026-10-10:

- Observation and Band Steering command histories render separately.
- The shared MAC filter hides and restores both lists.
- Expanded history and the filter survive automatic updates.
- A new observation at 35 seconds replaces the previous newest observation at 30 seconds without reloading the page.
- Device source timestamps advance automatically.
- The inspected browser warning/error log was empty.

The fixture uses simplified page styling. Real router boot, Wi-Fi stability, collection CPU cost and action-to-roaming behavior remain unverified. RSSI Kick action instrumentation remains incomplete.
- A controlled HTTP 503 history outage retained the last event rows, expanded history and MAC filter, with an explicit stale label. Removing the outage restored Current and newer rows automatically without reloading.
