# ZRAM lifecycle repair requirements

Source reviewed: `overlay/padavan-4.4/patches/zram-service.diff`.

The current start path ignores module loading, disksize writes, mkswap and swapon results. The stop path ignores swapoff results and attempts module removal regardless. Restart always proceeds to start after stop. Consequently an enabled setting cannot prove active swap, and restart can attempt to initialize a device that remains in use after swapoff fails.

Required repair:

1. Read `/proc/swaps` to establish whether `/dev/zram0` is active. Starting an already active device must not run mkswap on it.
2. Stop must return failure when swapoff fails or the device remains listed, preserve the device, and prevent restart from continuing.
3. Start must check module/device availability, disksize initialization, mkswap and swapon. Confirm the final `/proc/swaps` entry before reporting success.
4. Cleanup after a failed start must only reset a device confirmed inactive. Report each failure once through the system logger.
5. Keep saved `zram_enable` preferences intact. Runtime state and requested state are distinct.

Verify actual RC compilation and exercise failure paths for module loading, disksize, mkswap, swapon and swapoff. Router verification must demonstrate active swap, safe disable, restart and boot activation; build 215's BusyBox priority correction alone does not establish these behaviors.

No live router settings were changed during this review.

## Current implementation and evidence

The local `zram-service.diff` now checks active swap before initialization, prevents restart after failed swapoff or module removal, validates the disksize write and readback, checks mkswap/swapon results and confirms the final swap entry. It preserves saved preferences and logs activation failures.

`git apply --check` passed for the RC/WebUI hunks against `webui-audit/base`, and separately for the configure hunk against `dns-port-fixture-20261011`. These are two local source snapshots. Build 219 subsequently compiled the integration; the isolated lifecycle CI passed native ASan/UBSan execution with mocked system operations. Router execution remains unverified.

The Linux 4.4 ZRAM disksize store applies `PAGE_ALIGN`. Commit `932424a` corrects readback comparison to use the runtime page size. Regression CI run 38261975395 passed, including 123652 KiB total RAM producing 31657984 bytes of ZRAM. Full build 220 is pending. Build 219 must not be used as proof of successful swap activation on the observed hardware.
