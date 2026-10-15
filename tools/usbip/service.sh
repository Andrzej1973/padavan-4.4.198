#!/bin/sh
# Manual controller: boot/persistent enable and WebUI are not connected yet.
# Explicit guarded bind/unbind only; no automatic exports, NVRAM writes or force-kill fallback.
set -eu
umask 077
daemon=/sbin/usbipd
pidfile=/var/run/wr-usbip.pid
policy=/usr/libexec/wr-usbip/firewall-policy.sh
lock=/var/run/wr-usbip.lock

fail() { logger -t wr-usbip "$*"; return 1; }
snapshot()
{
    owned_pid=''
    if test -e "$pidfile" || test -L "$pidfile"; then
        test -f "$pidfile" && test ! -L "$pidfile" || { fail 'Invalid PID file'; return 1; }
        value=$(head -c 17 "$pidfile")
        case "$value" in ''|*[!0-9]*|0|1) fail 'Invalid PID value'; return 1;; esac
        test "${#value}" -le 10 || { fail 'Oversized PID'; return 1; }
        if test -d "/proc/$value"; then
            test "$(readlink "/proc/$value/exe" 2>/dev/null || :)" = "$daemon" || {
                fail 'PID executable mismatch'; return 1;
            }
            owned_pid=$value
        fi
    fi
    for candidate in $(pidof usbipd 2>/dev/null || :); do
        test "$candidate" = "$owned_pid" && continue
        # usbipd forks one worker for each accepted request.
        parent=$(awk '$1=="PPid:" {print $2}' "/proc/$candidate/status" 2>/dev/null || :)
        test -n "$owned_pid" && test "$parent" = "$owned_pid" &&
        test "$(readlink "/proc/$candidate/exe" 2>/dev/null || :)" = "$daemon" || {
            fail 'Untracked usbipd process; refusing action'; return 1;
        }
    done
}
start_service()
{
    snapshot || return 1
    test -z "$owned_pid" || { fail 'Owned daemon already running'; return 1; }
    test -x "$daemon" || { fail 'usbipd unavailable'; return 1; }
    lan=$(nvram get lan_ifname)
    wr_usbip_policy_apply "$lan" || { fail 'LAN policy failed'; return 1; }
    # The policy protects IPv4 only. Never start the default dual-stack daemon.
    if ! modprobe usbip-host || ! "$daemon" -4 -D --pid="$pidfile" 9>&-; then
        fail 'Startup failed; restrictive policy retained'
        return 1
    fi
    attempt=0
    while test "$attempt" -lt 10; do
        snapshot || return 1
        test -z "$owned_pid" || return 0
        sleep 1
        attempt=$((attempt + 1))
    done
    fail 'Startup unconfirmed; restrictive policy retained'
}
stop_service()
{
    snapshot || return 1
    if test -n "$owned_pid"; then
        kill -TERM "$owned_pid" || return 1
        attempt=0
        while test "$attempt" -lt 10; do
            snapshot || return 1
            test -n "$owned_pid" || break
            sleep 1
            attempt=$((attempt + 1))
        done
        test -z "$owned_pid" || { fail 'Stop timed out; policy retained'; return 1; }
    fi
    wr_usbip_policy_remove
}
test "$#" -gt 0 || exit 2
case "$1" in
    bind|unbind) test "$#" -eq 4 || exit 2;;
    start|stop|restart|status|reconcile) test "$#" -eq 1 || exit 2;;
    *) exit 2;;
esac
test -r "$policy" || { fail 'Policy unavailable'; exit 1; }
. "$policy"
exec 9>"$lock"
flock -x -n 9 || { fail 'Lifecycle busy'; exit 1; }
case "$1" in
    bind|unbind)
        test -r /usr/libexec/wr-usbip/device-policy.sh &&
        test -r /usr/libexec/wr-usbip/device-action.sh || exit 1
        . /usr/libexec/wr-usbip/device-policy.sh
        . /usr/libexec/wr-usbip/device-action.sh
        wr_usbip_device_action "$@" || { fail 'Device action failed or unconfirmed'; exit 1; };;
    start) start_service;;
    stop) stop_service;;
    restart) stop_service && start_service;;
    reconcile)
        if test "$(nvram get usbip_enable)" = 1; then
            snapshot || exit 1
            if test -z "$owned_pid"; then start_service; fi
        else
            stop_service
        fi;;
    status) snapshot && test -n "$owned_pid";;
esac
