# Candidate54 full replay and host composition

The full preparer chain completed on 2026-10-30 from
`.iot-local-check/full-driver-overlay4-20261029` to
`.iot-local-check/peer-retirement-chain54-20261030/peer-reset-executor`.
There are 53 actual preparer steps; protocol43 is a header, not a transform.
The `peer-chain.json` records script hashes and all candidate file hashes.
All 576 files match the incremental `peer-reset-executor54-20261030` tree.

Verified results on this fresh full candidate, using Windows host GCC
`-std=c11 -O2 -Wall -Wextra -Werror`:

| Result | Actual evidence directory | Scope |
| --- | --- | --- |
| 54 passed | `full54-host-20261030/result.json` | Existing extracted suite, including native/OS_ABL close bridges, physical/MBSS close chain and main-open seams |
| 4 passed | `full54-executor-targeted-20261030/result.json` | Table-close helper, executor model, both actual close bodies/wrappers, actual reset wrapper |
| 23 passed | `full54-composed-20261030/result.json` | Composed WDS and timer ownership regressions |

The 54-test run started before the four new checks were added to the suite;
those four ran separately with explicit `--only` selection. The current default
suite includes all 58. This report does not claim a single default58 run.

Updated the old source extractors to follow the real private close bodies plus
shared wrappers. Added shared synthetic adapter support rather than dropping
the old native/OS_ABL, physical chain and MBSS assertions. Reinitializing a peer
owner between independent fixture scenarios represents a fresh mock adapter;
no such reset was added to production code. An initial broad run stopped at the
old APShutdown extractor's public-function anchor; the extractor now checks
the actual private legacy body. The subsequent full54 run passed.

Fresh stage53 copies the shared executor header including the reviewed reset
lane. Stage54 accepts exactly the original incremental53 header hash or this
reviewed newer hash and records the actual input hash, preserving full replay
without relaxing arbitrary source pin checks.

These are sequential host checks with synthetic driver types, locks, MMIO,
task/IRQ operations and hardware responses. They do not prove kernel lock
ordering, callback/DMA retirement, target ABI or code size. No MIPS/OS_ABL
module build, firmware image, router change, build dispatch, commit or push.
The older full49-only status is superseded by this full54 replay.

Remaining work: serialize all relevant peer/radio admissions, bind and verify
adapter release, recover retained configured-WDS failures, verify configuration
and address-writer lifetime, then perform target and image gates before any
separately authorized device acceptance. IoT is not complete.
