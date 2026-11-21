# Beacon recovery lifecycle lease

The isolated MT7603 API candidate wraps existing APCheckBcnQHandler recovery
with an adapter-wide filter token. The lifecycle lease additionally prevents
admission of radio reset/PM teardown across that recovery operation.

Admission reserves active_tx under wr_iot_transition_lock before acquiring the
filter token under BcnRingLock. Locks never nest and vendor polling runs without
either lock. Contention rolls back only the newly reserved lease. Exact-token
completion releases the filter token before releasing its lease; stale completion
cannot decrement active_tx. Last release wakes both drain and ticket queues
outside locks. The gap between token release and lease release is conservative:
reset still sees the outstanding lease, and a new recovery reserves its own.

Source references: tools/iot/beacon-filter-owner-kernel.h and the generated
APCheckBcnQHandler wrapper in prepare-driver-api.py. The existing call site is
ap/ap_connect.c:APUpdateBeaconFrame. reset-admission.inc admits raw reset only
through radio_begin; prepare-radio-adapter-candidate.py waits for active_tx in
PM; prepare-pci-transaction-observation.py requires zero active_tx before bus
master disable. This lease does not pin adapter lifetime: existing caller
lifetime obligations remain required.

Host validation executes the generated wrapper with ASan/UBSan and injected
vendor body. It covers contention, reentry, stale token, exhausted token space,
early return, reset intent, real suspend admission and both last-release wakeups.
See evidence/WR1200JS-IOT-FILTER-LEASE-HOST-2026-11-08.json. These are sequential
interleaving fixtures with simulated locks, not a kernel concurrency proof.
Target compilation and physical reset/PM/PCI tests remain open. No RF silence,
late TxS retirement, firmware ACK reuse safety or production IoT acceptance is
claimed. No ACK or firmware protocol changes are made.
