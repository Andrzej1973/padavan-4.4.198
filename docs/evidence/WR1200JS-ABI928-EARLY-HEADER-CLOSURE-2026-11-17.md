# ABI928 early RC header closure

Run44166733507, revision1aa72c69798c86758f6f033b3ebbc4d19817ee9b,
failed `Verify experimental physical-stop host contracts` at
`check-initial-shutdown-headers.py`: `AssertionError: control-record-common.h`.
Monitor44167146042 identifies the same failed step and missing header.

The request envelope now includes common record declarations and edit codec.
`prepare-control.py` stages these, but early `prepare-rc.py` consumers use the
envelope before control/runtime preparation. Add common declarations, edit
record and resolver headers to that early stage. No driver or protocol change.

Both `check-initial-shutdown-headers.py` and
`check-initial-off-header-staging.py` completed exit0: recursive source-staging
closure and strict compilation from staged paths only. Add them to the new
edit suite so later transport changes cannot skip this early dependency check.
Fresh target verification remains required; no router acceptance is claimed.
