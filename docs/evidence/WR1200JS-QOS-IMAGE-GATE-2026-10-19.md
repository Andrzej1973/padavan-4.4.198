# WR1200JS QoS exact-image gate — 2026-10-19

The downloaded build #488 target BusyBox report lists
`CONFIG_FIRMWARE_INCLUDE_QOS=y`, `CONFIG_FIRMWARE_INCLUDE_IMQ=y` and
`CONFIG_FIRMWARE_INCLUDE_IFB=y`, but contains no QoS image gate. The WR1200JS
kernel configuration selects HTB, HFSC, TBF, ingress, classifiers, u32 match,
mirred and skbedit modules. The build workflow sets IFB, IMQ, IMQ behavior AB
and the Xtables IMQ target as modules.

Source recheck found a real packaging omission: the pinned
[iproute2 wrapper](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/iproute2/Makefile)
installs `/bin/tc` only for `CONFIG_FIRMWARE_INCLUDE_SQM=y`. The current
WR1200JS profile selects QoS while excluding SQM. The pinned
[inner Makefile](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/iproute2/iproute2-5.12.0/Makefile)
already compiles both `ip` and `tc`. No existing overlay recipe repaired that
conditional. This establishes a source packaging defect, not a fresh inspection
of the #488 filesystem.

`overlay/padavan-4.4/ports/qos/prepare-packaging.py` changes the installation
conditional to QoS OR SQM, preserves the existing `ip` install, is idempotent,
and rejects unexpected upstream recipes. It runs during WR1200JS source
preparation. It enables neither SQM nor a kernel scheduler and does not start
or alter QoS on the live router. CAKE remains excluded by the existing kernel
configuration gate.

`tools/check-target-busybox.py` now checks the effective kernel configuration
and final ROMFS when the QoS selector is active. It requires the exact
`/bin/tc` install path, executable permissions, little-endian MIPS ELF/library
closure, and a successful `tc -V` probe using target QEMU and ROMFS libraries.
It also requires the IMQ/IFB core configuration and each configured module
among the QoS qdisc/classifier/action set, with Linux case-sensitive names
from the pinned kernel Makefile and local IMQ patch. These checks do not
prove that QoS rules load, attach to the WAN, persist, or improve latency or
throughput. The gate runs inside the existing exact-image audit step in
`.github/workflows/build-padavan-4.4-wr1200js.yml`.

The local synthetic map check accepts a complete path inventory, rejects each
missing path, invalid core symbol, wrong `tc` path and wrong module-name case,
and skips the gate for an unselected QoS selector. On 2026-10-19:

- `py -3 tools/check-qos-packaging.py` passed GNU Make dry runs for QoS-only,
  SQM-only, both, neither and unset selectors, preserving `ip` installation.
- `py -3 tools/check-target-busybox-map.py` passed the service/SFE/QoS cases.
- In-memory Python AST parsing and `git diff --check` passed.

These are host checks; the new MIPS `tc` probe has not run against a new image.
No firmware compilation or router mutation was performed. A complete usable
QoS policy controller/WebUI, applied rules, lifecycle/persistence and physical
latency/load acceptance remain open; installing `tc` does not complete QoS.

## Controller source review

The verified local exact Git archive for the same pinned revision was inspected
without extracting another working tree. No QoS lifecycle implementation was
found in `trunk/user/rc/*.[ch]`; the named userspace QoS implementation is
[`sqm-qos/scripts/hwqos.sh`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/sqm-qos/scripts/hwqos.sh).
It hard-codes `br0`, writes whole packet marks with `--set-mark`, and manages
shared QDMA queues and direct FORWARD rules. Its original `run.sh` wrapper
also changes `hw_nat_mode`, commits NVRAM and reloads hardware NAT. These are
not suitable implicit side effects for an independently managed QoS service
alongside VPN/firewall policies. The existing project SQM wrapper is replaced
and SQM remains excluded; the old scripts were not enabled or copied into a
new controller. A scoped policy controller and its WAN/lifecycle integration
are still required, with explicit acceleration conflict handling, owned rules
and reversible failure recovery.
