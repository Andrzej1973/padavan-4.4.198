# IoT MT7603: reject removal of a closing netdev (2026-10-25)

In the isolated v38 candidate, `wr_iot_registry_begin_remove` rejected
`RESERVED` and `UNCERTAIN_OPEN` but accepted `CLOSING`. After a failed
`ndo_stop`, Linux 4.4 `dev_close` can clear `IFF_UP` regardless of the driver
result. A later removal that admits the same `CLOSING` record cannot rely on
`dev_close` to replay the unfinished ticket.

The host registry policy now refuses a new removal while the record is
`CLOSING`. Its checked continuation must first consume the reference and
return the record to `IDLE`; removal can then be admitted. The focused
`check-interface-registry.c` case verifies refusal before completion and
admission afterward. Strict C11 compilation with `-Wall -Wextra -Werror`
and execution passed.

`prepare-aux-remove-close-admission-candidate.py` copied v38 into isolated
`.iot-local-check/aux-remove-close-v39-20261025` and applied this one source
change. Python syntax passed; SHA-256 comparison of both trees showed exactly
`include/interface-registry.h` changed. The first comparison assertion used
POSIX separators on Windows and failed; the corrected comparison passed.

This avoids admitting a second teardown over an unresolved close. It does not
complete or schedule that close, make PCI `remove` honor the child result,
prove callback/adapter quiescence, compile the MIPS driver or validate the
router. Keep v39 out of the production image until the full retirement owner
and release path are implemented and verified.
