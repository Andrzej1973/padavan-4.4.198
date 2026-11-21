# Auxiliary removal close guard73 — host evidence

Candidate aux-remove73-20261030 derives from byte-verified composed70 source.
Pinned two-file transform covers ApCli_Remove and Monitor_Remove. Both now
call RtmpOSNetDevClose under RTNL and inspect the actual shared registry
close-phase helper before unregister. A failed ndo_stop can clear IFF_UP;
unregister does not propagate its return value. Therefore calling unregister
alone must not authorize freeing a still-owned interface.

Failure leaves netdev/vendor registration allocated, releases RTNL and returns
NDIS_STATUS_FAILURE before detach/free/flag clearing. Existing mark-removing
semantics mean automatic retry after a retained failure is still unbound.
This guard is necessary admission evidence, not callback retirement proof.
The subsequent success free path remains unaccepted until that separate
lifetime requirement is bound. MBSS already has an IDLE/terminal-close check
in wr_iot_mbss_begin_remove; it was not duplicated or changed by this step.

Strict GCC C11/O2/Wall/Wextra/Werror passed the extracted actual APCLI/Monitor
bodies plus actual wr_iot_netdev_close_phase_idle helper. Mark, RTNL, close,
free and vendor unregister remain mocked. Tests cover mark refusal, close
failure before detach/free and existing success operation order. A previous
seven-variant targeted run also passed parent failure propagation, native/ABL
legacy-close bridge and the earlier seam version. The stronger actual-helper
fixture subsequently passed separately. These are not target/ABI/runtime tests.

Main preparer now includes73, and the suite detects its extra test. Fresh
full73 preparation/replay has not been run; last full reproduced/tested tree
is70 (65 preparers/582 files,72+1 host variants). No production installation,
firmware build, router mutation, workflow dispatch, commit or push occurred.
Next bind shared callback retirement and retained-child retry/completion,
then root/final-work/physical PCI release receipts.
