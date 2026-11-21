# WR1200JS ZRAM runtime check — 2026-10-18

Read-only SSH check to `ASUS@192.168.20.1`. No service, setting, or router
state was changed.

Observed:

- Kernel: Linux `4.4.198`.
- Saved setting: `zram_enable=1`.
- `/proc/swaps` contains `/dev/zram0`, size `30912` KiB, usage `0` KiB,
  priority `32767`.
- `/proc/meminfo` reports `SwapTotal=30912` KiB and `SwapFree=30912` KiB.
- `/sys/block/zram0/disksize` is `31657984` bytes and `initstate` is `1`.

This confirms the configured ZRAM is currently initialized and active as swap.
It does not verify a disable/enable transition, behavior under memory pressure,
or persistence after reboot. Those checks remain for an approved device
acceptance window; no reboot or service restart was attempted.
