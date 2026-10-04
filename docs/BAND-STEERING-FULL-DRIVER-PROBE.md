# Full Band Steering driver compilation

The normal WR1200JS image is built and checked before an isolated copy of its kernel tree enables CONFIG_MT7603E_BAND_STEERING_7603 and CONFIG_RT_BAND_STEERING. The candidate applies the existing idle and grant readback preparations, runs olddefconfig, and builds vmlinux plus modules with the firmware MIPS toolchain. Gates require both driver modules, Band Steering symbols, recorded compiler commands containing -DBAND_STEERING, and unchanged baseline kernel configuration. Diagnostic modules are not installed in the firmware archive.

Local Python, YAML and shell syntax checks and configuration activation/rejection fixtures passed. Full driver compilation is pending CI. This does not establish Wi-Fi operation on a router. Profile ownership, service integration, WebUI and device acceptance remain pending.
