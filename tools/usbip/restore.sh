#!/bin/sh
# Sourced only by the lifecycle-lock owner. Never log private serials/table text.
wr_usbip_restore_unique()
(
    wr_usbip_restore_matches=0
    wr_usbip_restore_scanned=0
    for wr_usbip_candidate in /sys/bus/usb/devices/*; do
        wr_usbip_restore_scanned=$((wr_usbip_restore_scanned + 1))
        test "$wr_usbip_restore_scanned" -le 256 || return 1
        case "${wr_usbip_candidate##*/}" in usb*|*:*|*[!0-9.-]*) continue;; esac
        test -r "$wr_usbip_candidate/idVendor" && test -r "$wr_usbip_candidate/idProduct" || return 1
        wr_usbip_other_vendor=$(cat "$wr_usbip_candidate/idVendor") || return 1
        wr_usbip_other_product=$(cat "$wr_usbip_candidate/idProduct") || return 1
        test "$wr_usbip_other_vendor:$wr_usbip_other_product" = "$2:$3" || continue
        wr_usbip_device=$(readlink -f "$wr_usbip_candidate") || return 1
        wr_usbip_serial_read || return 1
        if test "$wr_usbip_serial_value" = "$4"; then
            wr_usbip_restore_matches=$((wr_usbip_restore_matches + 1))
        fi
    done
    test "$wr_usbip_restore_matches" -eq 1
)
wr_usbip_restore_preflight()
{
    wr_usbip_device_check "$1" || return 1
    test "$(cat "$wr_usbip_device/idVendor")" = "$2" || return 1
    test "$(cat "$wr_usbip_device/idProduct")" = "$3" || return 1
    wr_usbip_expected_serial=$4
    wr_usbip_serial_matches || return 1
    wr_usbip_restore_unique "$@"
}
wr_usbip_restore_exports()
{
    test "$(nvram get usbip_enable)" = 1 && test "$(nvram get usbip_restore)" = 1 || return 0
    snapshot || return 1
    test -n "$owned_pid" || return 1
    # Capture the whole validated table and exit status before any device action.
    wr_usbip_restore_table=$(/usr/libexec/wr-usbip/export-table --list 9>&-) || return 1
    test -n "$wr_usbip_restore_table" || return 0
    while IFS="$(printf '\t')" read -r wr_restore_bus wr_restore_vendor wr_restore_product wr_restore_serial; do
        wr_usbip_restore_preflight "$wr_restore_bus" "$wr_restore_vendor" "$wr_restore_product" "$wr_restore_serial" || return 1
    done <<EOF
$wr_usbip_restore_table
EOF
    while IFS="$(printf '\t')" read -r wr_restore_bus wr_restore_vendor wr_restore_product wr_restore_serial; do
        wr_usbip_restore_preflight "$wr_restore_bus" "$wr_restore_vendor" "$wr_restore_product" "$wr_restore_serial" || return 1
        wr_usbip_device_action bind "$wr_restore_bus" "$wr_restore_vendor" "$wr_restore_product" "$wr_restore_serial" || return 1
    done <<EOF
$wr_usbip_restore_table
EOF
    # Hotplug cannot be locked atomically with USB sysfs; partial success is possible.
    return 0
}
