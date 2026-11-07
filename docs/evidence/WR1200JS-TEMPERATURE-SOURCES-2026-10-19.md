# WR1200JS temperature sources — 2026-10-19

Read-only SSH inspection of the running Padavan 4.4.198 router:

- `iwpriv rai0 stat` reported `Current temperature = 39` for the active
  MT76x2 5 GHz radio at the time of inspection. It is a live snapshot, not
  a constant or a CPU measurement.
- `iwpriv ra0 stat` (MT76x3 2.4 GHz) did not report a temperature field.
- No `thermal_zone*/temp`, hwmon `temp*_input`, or temperature-named node
  was found under the inspected `/sys` and `/proc` trees. The filtered kernel
  log gave no CPU thermal sensor indication. This establishes only that no
  supported CPU reading was exposed by this running image through the paths
  checked; it does not prove that the silicon has no temperature sensor.

For the Padavan Modern status card, show a live 5 GHz reading only after an
actual backend read with an explicit source label. Show CPU, 2.4 GHz, and
"system" temperatures only if a separate trustworthy source is identified
and validated on WR1200JS. Keep demo values labelled DEMO; never turn the
reference-image numbers into claimed device measurements. Do not alter the
Classic theme or expose an unverified control.
