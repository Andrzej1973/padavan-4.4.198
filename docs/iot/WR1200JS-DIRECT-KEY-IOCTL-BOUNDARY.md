# Direct key ioctl boundary

Focused source/host review, 2026-11-18. This is an open integration requirement,
not a device race reproduction or a completed fix.

`mcu-control-admission.inc:wr_iot_control_enter` counts live control actors and
excludes transition/reset/PM. It intentionally permits multiple actors and does
not check the ra2 key arbiter. `prepare-mcu-control-admission.py` wraps the public
`rt28xx_ioctl` using that admission. The Linux API producer keeps this wrapper
for ordinary ioctls. Therefore this outer lifetime fence alone cannot prove
that direct key writes exclude the requested/periodic GTK writer.

Pinned vendor `ap/ap_cfg.c` contains HOSTAPD_OID_SET_KEY and
HOSTAPD_OID_DEL_KEY under HOSTAPD_SUPPORT, including direct MAC lookup and
key table changes. Pinned os/linux/config.mk defaults HAS_HOSTAPD_SUPPORT=n.
Actual per-unit effective macro reports are being added to the optional build;
source defaults are not proof of final target exclusion. Other native setters
also mutate shared-key configuration and need classification by their guards
and callers before claiming complete configuration/key serialization.

`tools/iot/check-control-key-exclusion-gap.c` executes the actual counted
admission with a boundary adapter. With one active GTK key owner/reference, a
second generic control caller enters and exits without changing the key flag.
ASan/UBSan host check passes by confirming this counterexample. It does not
execute an ioctl, emulate parallel CPU execution or assert firmware behavior.

Next implementation boundary: classify reachable mutation commands before the
first native state change, bind the exact BSS/adapter and retain the same ra2
arbiter through native execution. Preserve query behavior and Main/Guest paths.
Global setters that can affect ra2 require explicit classification; netdev name
alone is insufficient. Do not hold table/transition spinlocks across user copy,
crypto, timer cancellation or hardware writes. Do not globally change counted
control admission: independent control actors and nested MCU sends depend on it.
Queued EAPOL generation validation remains a separate implemented boundary.
