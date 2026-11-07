# Full candidate58 replay, host suite and adapter-release audit

Full replay completed from `full-driver-overlay4-20261029` into
`peer-retirement-chain58-20261030/peer-delete-execution`: 56 actual preparers,
578 files. Rejected57 is excluded. Compared with the incrementally prepared58
tree, the sole difference is the added marker line
`#define WR_IOT_DELETE_EXECUTION_LEASE 1` in the deletion include; all C bodies
and all other files match byte-for-byte. Both variants of the resume contract
were compiled/run again on the fresh full tree.

Actual strict host GCC results:

| Result | Evidence directory under `.iot-local-check` | Scope |
| --- | --- | --- |
| 61 passed | `host58-full-incremental-20261030/result.json` | Full extracted suite on incremental58, including all five native/OS_ABL/diagnostic/HNAT bridge variants |
| 2 passed | `full58-resume-marker-20261030/result.json` | Both resume-contract variants on freshly replayed58 including the marker |
| 23 passed | `full58-composed-20261030/result.json` | Composed WDS/timer checks on freshly replayed58 |

Seven Python files parsed and targeted `git diff --check` passed. This is not
a claim that a second full61 suite ran on the fresh tree. Kernel primitives,
hardware and layouts remain mocked; no MIPS/OS_ABL target module or firmware
build, real concurrency/DMA/callback proof, or device acceptance.

## Adapter release remains an open gate

The existing `check-pci-remove-release-gate.py` returned1 on58:
`OPEN GATE: first join, root detach, final join and release claim are not ordered before adapter free`.

New lexical `audit-peer-adapter-release.py` recorded actual file hashes and
five bare, unchecked release calls in `peer-adapter-release58-audit.json`:

| Source | Line | Call |
| --- | --- | --- |
| `common/rtmp_init.c` | 2522 | `RTMPFreeAdapter` |
| `os/linux/pci_main_dev.c` | 394 | `RTMPFreeAdapter` (probe unwind) |
| `os/linux/pci_main_dev.c` | 564 | `RtmpRaDevCtrlExit` (remove) |
| `os/linux/sdio_main_dev.c` | 163 | `RTMPFreeAdapter` |
| `os/linux/sdio_main_dev.c` | 190 | `RtmpRaDevCtrlExit` |

This is a full-source inventory, not a claim that SDIO is enabled on WR1200JS.
Native declaration, OS_ABL ops field and implementation of RTMPFreeAdapter all
return VOID. `os/linux/rt_profile.c:1717` frees MacTabLock before adapter memory
and cookie release. RtmpRaDevCtrlExit destroys semaphore state, frees probe-IE
allocations and optionally rings before calling RTMPFreeAdapter, then returns
TRUE without an observable free result. A late refusal only inside free would
therefore be insufficient and could let callers unmap CSR/release resources.

Next work must claim release before the first controller destructor, propagate
refusal coherently through native/OS_ABL and callers, and distinguish cold probe
unwind from initialized teardown. That requires actual peer/task/callback/
registry/DMA retirement evidence and a fence against new owners; the lexical
audit and completed software close cannot substitute for it. No release gate
was disabled or marked accepted. No router changes, dispatch, commit or push.
