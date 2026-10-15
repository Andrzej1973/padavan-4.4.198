#!/bin/sh
# Sourced by wr-usbip. Caller must serialize lifecycle and start usbipd with -4.
# Apply before startup; remove only after the owned daemon is confirmed stopped.
# Owns WRUSBIP_INPUT only; never flush INPUT or change its default policy.

wr_usbip_policy_apply()
{
    wr_usbip_lan="$1"
    case "$wr_usbip_lan" in
        ''|lo|*[!a-zA-Z0-9_.:-]*) return 1 ;;
    esac
    test "${#wr_usbip_lan}" -le 15 || return 1
    test -d "/sys/class/net/$wr_usbip_lan" || return 1
    type iptables >/dev/null 2>&1 || return 1
    type iptables-restore >/dev/null 2>&1 || return 1
    wr_usbip_existing=$(iptables -S INPUT) || return 1
    wr_usbip_hooks=$(printf '%s\n' "$wr_usbip_existing" |
        awk '$0 == "-A INPUT -j WRUSBIP_INPUT" {n++} END {print n+0}')
    test "$wr_usbip_hooks" -le 32 || return 1
    {
        printf '*filter\n:WRUSBIP_INPUT - [0:0]\n'
        printf '%s\n' '-A WRUSBIP_INPUT -i lo -p tcp --dport 3240 -j RETURN'
        printf '%s\n' "-A WRUSBIP_INPUT -i $wr_usbip_lan -p tcp --dport 3240 -j RETURN"
        printf '%s\n' '-A WRUSBIP_INPUT -p tcp --dport 3240 -j DROP'
        printf '%s\n' '-A WRUSBIP_INPUT -j RETURN'
        while test "$wr_usbip_hooks" -gt 0; do
            printf '%s\n' '-D INPUT -j WRUSBIP_INPUT'
            wr_usbip_hooks=$((wr_usbip_hooks - 1))
        done
        printf '%s\n' '-I INPUT 1 -j WRUSBIP_INPUT' 'COMMIT'
    } | iptables-restore --noflush --wait=5
}

wr_usbip_policy_remove()
{
    type iptables >/dev/null 2>&1 || return 1
    type iptables-restore >/dev/null 2>&1 || return 1
    wr_usbip_existing=$(iptables -S INPUT) || return 1
    wr_usbip_hooks=$(printf '%s\n' "$wr_usbip_existing" |
        awk '$0 == "-A INPUT -j WRUSBIP_INPUT" {n++} END {print n+0}')
    test "$wr_usbip_hooks" -le 32 || return 1
    # Keep an empty owned chain: avoids deleting references owned by another tool.
    {
        printf '*filter\n:WRUSBIP_INPUT - [0:0]\n'
        while test "$wr_usbip_hooks" -gt 0; do
            printf '%s\n' '-D INPUT -j WRUSBIP_INPUT'
            wr_usbip_hooks=$((wr_usbip_hooks - 1))
        done
        printf '%s\n' 'COMMIT'
    } | iptables-restore --noflush --wait=5
}
