# WR1200JS SFE exact-image gate — 2026-10-19

Build #488's target BusyBox report recorded `CONFIG_FIRMWARE_INCLUDE_SFE=y`
but had no exact-image assertion for SFE. The report therefore listed SFE as
an entrypoint gap; its successful build did not prove the SFE module set was
present.

The pinned Padavan source at
[`c25283e915a2a00a763774dd255b14aff997285e`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/rc/net.c)
shows the `sfe_enable` path asking `module_smart_load("fast_classifier", NULL)`
and writing `/sys/fast_classifier/skip_to_bridge_ingress`. Its
[`common_ex.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/rc/common_ex.c)
calls `modprobe` for module loading. The pinned
[`shortcut-fe/Makefile`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/net/shortcut-fe/Makefile)
builds `fast-classifier`, `shortcut-fe`, `shortcut-fe-ipv6`, and
`shortcut-fe-cm`; the pinned [`rc/Makefile`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/rc/Makefile)
installs the controller as `/sbin/rc`.

`tools/check-target-busybox.py` now checks the final ROMFS for `/sbin/rc`, all
four SFE `.ko` modules under `/lib/modules`, and the exact-image BusyBox
`modprobe` applet whenever SFE is selected. Its report scope explicitly limits
this to image packaging; it does not claim module loading, traffic offload or
throughput. The local synthetic gate rejects each missing module, the missing
controller and missing `modprobe`. The check is part of the existing WR1200JS
BusyBox audit job and its workflow path filter already includes the shared
service-map helper.

Local checks passed on 2026-10-19:

- `py -3 tools/check-target-busybox-map.py`
- `py -3 -m py_compile tools/target_busybox_service_map.py tools/check-target-busybox.py tools/check-target-busybox-map.py`
- `git diff --check -- tools/check-target-busybox.py tools/check-target-busybox-map.py tools/target_busybox_service_map.py`

No new firmware image has run this gate yet. The #488 artifact remains the
previous baseline and still has no SFE assertion. A separate local QoS
exact-image gate has since been added; its build evidence is pending. Router-
side SFE loading, hardware offload, performance and stability remain
unverified; no setting was changed.
