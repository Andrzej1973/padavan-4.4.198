# Published child-family snapshot62 — begin only

Pinned `prepare-pci-child-snapshot.py` creates
`.iot-local-check/pci-child-snapshot62-20261030` from61. The PCI remove path
calls the new snapshot after WORK_JOINED and before RtmpPhyNetDevExit.
Under the shared transition lock it requires retirement fenced, zero
registration inflight and the expected PCI phase; it validates registry
identity/generation/publication/family and constructs the published-family mask.
Multiple BSS records contribute one MBSS family bit. Unknown, unpublished or
inconsistent records refuse without changing child teardown state.

Only `wr_child_teardown_begin` is called. Nonempty families remain DRAINING;
no close/completion bits or callback receipts are manufactured. An empty child
registry follows the existing zero-family model; proving that the registry
covers every vendor child allocation remains a separate necessary condition.

Two selected strict GCC host checks passed in
`pci-child-snapshot62-targeted/result.json`: exact helper snapshot cases
(including duplicate family, unknown/unpublished identity, registration fence,
empty set and replay refusal), and extracted actual preceding work-join block
with source-order assertion before the snapshot and root detach.

Source audit of actual removals:

- WDS unregisters then retains allocation/vendor registration and records
  `wr_iot_registry_after_unregister`; it returns failure pending callback reaper.
- MBSS still unregisters, unregisters vendor wdev and frees the netdev after
  its beacon/close gates, without the equivalent final registry release proof.
- AP-client and Monitor similarly proceed from unregister to vendor unregister
  and netdev free without a bound final registry-release/callback receipt.

Thus a successful family-return value alone is not accepted as completion.
Next reconcile these per-family lifetime paths and vendor/registry coverage
before recording family close/completion, then root callback and final PCI
release receipts. This source audit is not proof that any callback actually
ran after free. Kernel work, hardware and layouts are modeled. No target,
firmware, runtime/device acceptance, router changes, dispatch, commit or push.
Step62 is in the chain; latest full replay remains58.
