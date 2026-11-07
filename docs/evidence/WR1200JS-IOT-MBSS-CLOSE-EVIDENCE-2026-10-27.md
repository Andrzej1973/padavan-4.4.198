# WR1200JS IoT: per-BSS close evidence before MBSS removal — 2026-10-27

The host-only all-child teardown model previously accepted one caller Boolean
for the whole MBSS family. That did not itself reject a still-owned second BSS.
`tools/iot/mbss-close-evidence.h` now requires every published MBSS registry
record to be idle, with no close in progress or removal already begun. It also
requires the caller-proven published MBSS count to match and the recovery owner
to be joined. A published unknown-family record blocks the proof. An
unpublished MBSS record with a live or uncertain reference blocks it too.

`check-all-child-teardown.c` covers two BSS records, including one still owned,
one closing, a count mismatch, an unjoined recovery owner, a running close and
an unpublished uncertain open. The successful case feeds the computed proof to
the existing family close gate.

Verification: `gcc -std=c11 -Wall -Wextra -Werror -pedantic -I tools/iot
tools/iot/check-all-child-teardown.c -o <temporary executable>` and execution
both exited 0; `git diff --check` exited 0. This is a Windows host C11 check.
No MIPS target build, production driver binding, image check or router runtime
test occurred. The production caller must still obtain the exact published
count under the shared adapter lock, fence new opens, join checked close and
recovery, then bind this proof before `RT28xx_MBSS_Remove`. The Boolean inputs
remain caller claims until that binding is reviewed.

## Follow-up: checked DOWN must be proven

Review of the prepared v42 driver showed that `wr_iot_mbss_begin_remove()`
already rejects a registry entry with an acquired open token unless the
checked close reached stage 4 (or the open was proven unmutated). The host
family proof now applies that same condition to **every** published MBSS
record. A fixture with an idle record, acquired token and incomplete close
fails; setting close stage 4 passes. Strict C11 compilation and execution
again exited 0.

The vendor source exposes the candidate count through non-null
`pAd->ApCfg.MBSSID[i].wdev.if_dev` entries and records through
`pAd->wr_iot_interface_refs`, serialized by `wr_iot_transition_lock`. That
identifies a possible production preflight, but it is not sufficient alone:
`rt_pci_remove()` still ignores `RtmpPhyNetDevExit()` failure and frees adapter
and MMIO. A failed global preflight could therefore leave child callbacks
pointing at freed memory. Bind this proof only with a complete PCI remove
close/join/terminal policy and a target failure-injection test.
