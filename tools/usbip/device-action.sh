#!/bin/sh
# Sourced under the lifecycle lock by wr-usbip; never called from an EJ getter.
wr_usbip_device_action()
{
    test "$#" -eq 4 || return 1
    wr_usbip_action=$1
    wr_usbip_bus=$2
    wr_usbip_vendor=$3
    wr_usbip_product=$4
    case "$wr_usbip_action" in bind|unbind) ;; *) return 1;; esac
    for wr_usbip_hex in "$wr_usbip_vendor" "$wr_usbip_product"; do
        test "${#wr_usbip_hex}" -eq 4 || return 1
        case "$wr_usbip_hex" in *[!0-9a-fA-F]*) return 1;; esac
    done
    snapshot || return 1
    if test "$wr_usbip_action" = bind; then
        test -n "$owned_pid" || return 1
    fi
    wr_usbip_device_check "$wr_usbip_bus" || return 1
    # Compare the identity the user observed; never act on just a recycled bus ID.
    test "$(cat "$wr_usbip_device/idVendor")" = "$wr_usbip_vendor" || return 1
    test "$(cat "$wr_usbip_device/idProduct")" = "$wr_usbip_product" || return 1
    wr_usbip_driver=''
    if test -L "$wr_usbip_device/driver"; then
        wr_usbip_driver=$(readlink "$wr_usbip_device/driver") || return 1
    fi
    if test "$wr_usbip_action" = unbind; then
        test "${wr_usbip_driver##*/}" = usbip-host || return 1
        # Kernel SDEV_ST_AVAILABLE=1; refuse active, error and unknown states.
        test "$(cat "$wr_usbip_device/usbip_status")" = 1 || return 1
    elif test "${wr_usbip_driver##*/}" = usbip-host; then
        return 0
    fi
    /sbin/usbip "$wr_usbip_action" -b "$wr_usbip_bus" 9>&- || return 1
    test "$(cat "$wr_usbip_device/idVendor")" = "$wr_usbip_vendor" || return 1
    test "$(cat "$wr_usbip_device/idProduct")" = "$wr_usbip_product" || return 1
    wr_usbip_driver=''
    if test -L "$wr_usbip_device/driver"; then
        wr_usbip_driver=$(readlink "$wr_usbip_device/driver") || return 1
    fi
    if test "$wr_usbip_action" = bind; then
        test "${wr_usbip_driver##*/}" = usbip-host
    else
        test "${wr_usbip_driver##*/}" != usbip-host
    fi
}
