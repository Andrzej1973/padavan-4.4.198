# WR1200JS CPU frequency policy

Decision approved by the project owner on 2026-10-04.

The central WR1200JS configuration no longer advertises these selectors:

- `CONFIG_FIRMWARE_CPU_SLEEP`: the selector was a port request, not an operational feature in the main 4.4 image. The isolated systick candidate remains available for research; it is not required for project completion.
- `CONFIG_FIRMWARE_INCLUDE_MT7621_CPUFREQ`: no integrated package hook exists in the current port. The Hadzhioglu utility manually writes PLL registers through `/dev/mem`; it is not an automatic frequency governor.
- `CONFIG_FIRMWARE_CPU_900MHZ`: this commented selector requested forcing 900 MHz instead of the bootloader-selected frequency. That is not necessarily overclocking and provides no improvement if the CPU already runs at that frequency.

Keep the bootloader-selected frequency. This configuration cleanup introduces no clock-register writes and does not enable overclocking. Normal MIPS idle WAIT is separate from frequency scaling. Actual device frequency and energy savings have not been measured. Existing kernel clock initialization remains subject to its own configuration; removing firmware selectors is not proof of a changed hardware frequency.

The config verifier retains its CPU_SLEEP port-pending diagnosis for users who add the unsupported selector back in their own forks.
