# Full candidate70 preparation and child retirement inventory72

Fresh main-chain preparation completed65 preparers and582 files. All files
are byte-identical to incremental nettask-init70d-20261030; peer-chain.json
matches the independently computed SHA256 inventory. Result:
.iot-local-check/full70-comparison72.json. Thus the72-variant host replay
and separate1-variant injected-exit test apply to the same source bytes as
this fresh candidate. This is source reproducibility and extracted host
verification, not MIPS compilation, module linking, image or runtime proof.
The composed chain now ends70; earlier notes saying64 describe prior state.
Draft65 late tasklet join remains excluded. No production overlay installed.

## Next concrete lifetime gap

Lexical function-body inventory (not a concurrency verifier):

| Family | Source function | Frees netdev | Registry after-unregister transition |
| --- | --- | --- | --- |
| MBSS | ap/ap_mbss.c:207 | True | False |
| APCLI | ap/ap_apcli.c:3470 | True | False |
| WDS | ap/ap_wds.c:1468 | False | True |
| Monitor | sniffer/sniffer_radiotap.c:480 | True | False |

WDS explicitly retains allocation/vendor registration and returns failure
because callback join/reaper binding is missing. MBSS, APCLI and Monitor
proceed to vendor unregister/free. Returned RTNL/netdev reference draining
only covers kernel-accounted references; it does not prove vendor raw wdev
readers, timers, tasklets, IRQ/DMA or recovery owners have retired.
Do not set WR_CHILD completion or RELEASE_CLAIMED merely because a remove
function returned success. Next bind common callback retirement evidence and
family completion, including safe retry of retained WDS, before final PCI
release. Preserve tasklet early join and the new final submission fence.

The inventory with exact source hashes is local child-retirement72-inventory.json.
No router mutation, firmware build, CI dispatch, commit or push in this step.
WSL listing probe returned installer usage and exit1; no usable distribution
or target compiler was established by that probe. No installation attempted.
