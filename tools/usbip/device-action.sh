#!/bin/sh
# Sourced under the lifecycle lock by wr-usbip; never called from an EJ getter.
wr_usbip_serial_matches()
{
    # Pinned BusyBox enables hexdump; its minimal od lacks -A/-t/-N.
    type hexdump >/dev/null 2>&1 || return 1
    wr_usbip_serial_value=$(hexdump -v -n 258 -e '1/1 "%02x"' "$wr_usbip_device/serial") || return 1
    case "$wr_usbip_serial_value" in *0a) wr_usbip_serial_value=${wr_usbip_serial_value%0a};; esac
    test -n "$wr_usbip_serial_value" && test "${#wr_usbip_serial_value}" -le 512 || return 1
    wr_usbip_serial_tail=$wr_usbip_serial_value
    while test -n "$wr_usbip_serial_tail"; do
        wr_usbip_serial_rest=${wr_usbip_serial_tail#??}
        wr_usbip_serial_byte=${wr_usbip_serial_tail%"$wr_usbip_serial_rest"}
        case "$wr_usbip_serial_byte" in 0?|1?|7f) return 1;; esac
        wr_usbip_serial_tail=$wr_usbip_serial_rest
    done
    test "$wr_usbip_serial_value" = "$wr_usbip_expected_serial"
}
wr_usbip_device_action()
{
    test "$#" -eq 4 || test "$#" -eq 5 || return 1
    wr_usbip_action=$1
    wr_usbip_bus=$2
    wr_usbip_vendor=$3
    wr_usbip_product=$4
    wr_usbip_expected_serial=${5-}
    if test "$#" -eq 5; then
        test -n "$wr_usbip_expected_serial" && test "${#wr_usbip_expected_serial}" -le 512 || return 1
        test "$(( ${#wr_usbip_expected_serial} % 2 ))" -eq 0 || return 1
        case "$wr_usbip_expected_serial" in *[!0-9a-f]*) return 1;; esac
    fi
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
    test -z "$wr_usbip_expected_serial" || wr_usbip_serial_matches || return 1
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
    test -z "$wr_usbip_expected_serial" || wr_usbip_serial_matches || return 1
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
