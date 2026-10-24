# IoT transition owner: main close still mutates outside the ticket

After the successful isolated MIPS build `40080616642`, source inspection
found a remaining all-mutator gap in the same candidate. This is a source
finding, not a reproduced device race.

`tools/iot/mbss-open-admission.inc` now reserves a `WR_RADIO_BSS_OPEN`
ticket, observes the main MT7603 configuration outside the short lock, then
rechecks epoch, serial, main readiness and close/reset intent before raw open.
Its ticket prevents **participating** transitions from entering concurrently.

`tools/iot/prepare-radio-adapter-candidate.py` currently inserts
`wr_iot_radio_main_down()` near the start of `MainVirtualIF_close`. That
invalidates the epoch and clears `main_ready`, and the host fixture checks
that it happens before the first main-close mutation. But the generated main
close wrapper does not acquire a `WR_RADIO_CLOSE` or other exclusive ticket,
does not wait for a previously admitted BSS-open owner to retire, and then
continues its `RTMPInfClose` / `VIRTUAL_IF_DOWN` path. A main-close intent
arriving after the IoT wrapper's second check may therefore race with the
raw BSS-open mutation. Reset uses the ticket-aware wrapper in
`tools/iot/reset-admission.inc`, but its coverage of all direct reset and
PM/watchdog callers still requires audit.

The next source change must make main close participate in the same
transition owner and preserve mandatory ndo_stop cleanup. It must publish
close intent before any mutation, defer the destructive close until the
current ticket retires, retain adapter/netdevice references, and avoid
waiting while holding the short lock or a worker join dependency. Test a
close request before observation, during observation, after revalidation but
before raw open, and during raw open, then compile the assembled target
driver. A local sequential host fixture or the green MIPS link alone cannot
prove this interleaving safe.

No production driver, firmware image or router state was changed here.
