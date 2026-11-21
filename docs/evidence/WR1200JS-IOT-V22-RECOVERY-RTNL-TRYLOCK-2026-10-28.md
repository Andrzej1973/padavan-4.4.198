# IoT main recovery RTNL admission — isolated v22, 2026-10-28

The v21 recovery callback invoked checked close without RTNL, although ordinary main open/stop and netdevice teardown use that lock. Blocking `rtnl_lock` in the worker would risk a `cancel_work_sync` join cycle. The isolated v22 candidate `.iot-local-check/mt7603-main-recovery-rtnl-v22-20261028` stages nonblocking `rtnl_trylock` around the existing callback executor and `rtnl_unlock` afterward. On contention it records a retained owner under the transition lock, without starting a hardware action or spending a recovery attempt. It never waits for RTNL inside the callback. A stopped owner remains stopped. This is one part of the lifetime protocol, not a complete worker binding.

The shared `tools/iot/main-open-recovery-owner.h` adds `wr_iot_main_recovery_rtnl_unavailable`. `tools/iot/prepare-main-recovery-rtnl-candidate.py` verified all 67 v21 input hashes and copied them to v22. Only `include/main-open-recovery-owner.h` and `os/linux/rt_main_dev.c` differ; all 67 v22 output hashes match the composition manifest. `production_installed=false`, `main_recovery_queue_bound=false` and `pci_release_gate_bound=false`.

Checks run:

- Strict C11 `check-main-open-recovery-owner.c` against v22 headers: pass. This covers no attempt increment, retained pin, retry only after joined work, and existing exact-ticket ownership transitions.
- `prepare-main-recovery-rtnl-check.py` extracted the actual staged callback body. Its strict C11 host fixture passed RTNL contention, successful acquisition/unlock, and stopped-owner cases. The `rtnl_trylock` and executor are mocked; this is callback control-flow proof only.
- The extracted-callback fixture now also models the queue/RTNL race: producer still holds RTNL when work runs, callback retains the owner, a requeue without prior work join is rejected, and a joined external retry runs after RTNL becomes available. This is a deterministic host interleaving, not a live kernel scheduling result.
- Both preparer Python files compiled with `py_compile`; source composition hashes matched 67/67. `git diff --check` passed for tracked files touched here.

Open: v22 still has no actual queue/schedule call site, no accepted-work accounting at the caller, no netdev hold paired with `dev_put`, no bounded external retry/reaper, and no PCI removal completion path. RTNL contention converts the owner to retained. A worker queued inside `ndo_open` can therefore race before `ndo_open` drops RTNL and finish retained on its first run; queueing alone does not make recovery live. A future external reaper must join the callback and retry or reconcile it. A target MIPS build, firmware image and device runtime were not performed. Do not install or package v22 yet.
