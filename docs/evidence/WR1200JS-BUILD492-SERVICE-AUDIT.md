# WR1200JS build #492 service/image evidence — 2026-10-20

[Run 39325639006](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39325639006)
completed successfully, including firmware compilation, image verification,
downloads and firmware/config ZIP packaging. PR head was
`df70def328b9511d81c31483c6354f066bcac5b7`; the image report identifies the PR
merge revision `56d3559634014cb45e343bb0fab1d9fb3e88f80e`.

## Build #491 repair confirmed

Build #491 failed after make completed because an unrestricted compiler search
selected the ccache wrapper. Deriving `nm` from that wrapper's directory pointed
to a nonexistent executable. Commit `df70def` restricts all 14 affected compiler
lookups to the toolchain bin directory. In #492 both the firmware step and the
subsequent RSSI image verification passed. This confirms this CI repair, not
physical RSSI Kick behavior.

## Independently downloaded report

Artifact `target-busybox-audit`, ID `12222841162`, was downloaded into
`.audit-build492-exact/`. Source JSON SHA256:
`77aaf65cc73accf766a885d7b57ece621109053cd6ef93145662ed678b63c5aa`.
The adjacent JSON preserves selected report fields and provenance.

The report records 57 shell scripts, 150 applets, all 12 active service groups
mapped, no entrypoint gaps, and `success:true`. BusyBox is 1.24.2; binary and
effective-config SHA256 values are preserved in the adjacent JSON. QoS checks
confirm all 15 module paths and core config, executable MIPS `/bin/tc`, image
library closure, and `tc -V` under QEMU. SFE confirms its four modules, rc and
modprobe presence. WPAD and ZRAM image gates passed.

Successful job metadata also confirms final-image checks for SSH, iPerf3,
discovery/KMS, USB/IP settings, Stubby, DoH, Privoxy, ZeroTier, VPN profile tools,
settings backup, translations and routes. These are CI gate results; the
individual non-BusyBox artifacts were not downloaded in this step.

## Open acceptance

`runtime_verified:false` and `whole_service_audit_complete:false` remain
explicit. Invalid-action dispatch probes do not exercise start/stop/restart,
locking or daemon failure recovery. The two Lua utilities remain outside shell
coverage. Physical QoS/SFE traffic, service interactions, browser behavior,
persistence and reboot acceptance remain open. No router state was changed.
The generated firmware artifact still carries `_TEST`; this run does not
resolve the separately requested delivery naming change.
