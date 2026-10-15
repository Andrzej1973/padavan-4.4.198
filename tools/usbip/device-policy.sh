#!/bin/sh
# Candidate bind preflight. Read-only; does not change drivers or export devices.
# Caller must serialize with the lifecycle lock and re-check before usbip bind.
wr_usbip_device_check()
{
    test "$#" -eq 1 || return 1
    wr_usbip_id=$1
    case "$wr_usbip_id" in ''|*[!0-9.-]*) return 1;; esac
    test "${#wr_usbip_id}" -le 31 || return 1
    printf '%s\n' "$wr_usbip_id" | awk '
        /^[0-9]+-[0-9]+(\.[0-9]+)*$/ {ok=1}
        END {exit !ok}' || return 1
    wr_usbip_device=$(readlink -f "/sys/bus/usb/devices/$wr_usbip_id") || return 1
    test -n "$wr_usbip_device" && test -d "$wr_usbip_device" || return 1
    wr_usbip_class=$(cat "$wr_usbip_device/bDeviceClass") || return 1
    case "$wr_usbip_class" in
        [0-9a-fA-F][0-9a-fA-F]) ;;
        *) return 1;;
    esac
    test "$wr_usbip_class" != 09 || return 1
    test -r /proc/self/mountinfo && test -r /proc/swaps || return 1
    test -d /sys/class/block && test -r /sys/class/block || return 1
    # Check every partition separately: its major:minor identifies mounted use.
    for wr_usbip_block in /sys/class/block/*; do
        test -e "$wr_usbip_block" || continue
        wr_usbip_path=$(readlink -f "$wr_usbip_block") || return 1
        case "$wr_usbip_path" in
            "$wr_usbip_device"/*)
                wr_usbip_devnum=$(cat "$wr_usbip_block/dev") || return 1
                printf '%s\n' "$wr_usbip_devnum" | awk '/^[0-9]+:[0-9]+$/ {ok=1} END {exit !ok}' || return 1
                if awk -v device="$wr_usbip_devnum" '$3==device {used=1} END {exit used?0:1}' /proc/self/mountinfo; then
                    return 1
                else
                    wr_usbip_result=$?
                fi
                test "$wr_usbip_result" -eq 1 || return 1
                # A swap block device may be active without being mounted.
                wr_usbip_swaps=$(awk 'NR>1 {print $1}' /proc/swaps) || return 1
                for wr_usbip_swap in $wr_usbip_swaps; do
                    wr_usbip_swap_path=$(readlink -f "$wr_usbip_swap") || return 1
                    test "${wr_usbip_swap_path##*/}" != "${wr_usbip_block##*/}" || return 1
                done
                ;;
        esac
    done
    # Exporting a USB NIC or modem can remove management/WAN connectivity.
    for wr_usbip_classdir in /sys/class/net /sys/class/tty; do
        test -d "$wr_usbip_classdir" && test -r "$wr_usbip_classdir" || return 1
        for wr_usbip_member in "$wr_usbip_classdir"/*/device; do
            test -e "$wr_usbip_member" || continue
            wr_usbip_path=$(readlink -f "$wr_usbip_member") || return 1
            case "$wr_usbip_path" in
                "$wr_usbip_device"|"$wr_usbip_device"/*) return 1;;
            esac
        done
    done
    # Preflight is not an atomic claim: hotplug and open-device races remain.
    return 0
}
