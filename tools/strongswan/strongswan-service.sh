#!/bin/sh
# Managed default charon/starter instance only. Never rewrite existing profiles.
set -eu
umask 077
ipsec=/usr/sbin/ipsec
starter=/usr/libexec/ipsec/starter
charon=/usr/libexec/ipsec/charon
config=/etc/storage/strongswan/ipsec.conf
starter_pid=/var/run/starter.charon.pid
charon_pid=/var/run/charon.pid
lock=/var/run/wr-strongswan.lock

fail() { logger -t StrongSwan "$*"; return 1; }
owned()
{
    test -e "$1" || return 0
    test -f "$1" && test ! -L "$1" || { fail 'Invalid PID file'; return 1; }
    value="$(head -c 17 "$1")"
    case "$value" in ''|*[!0-9]*|0|1) fail 'Invalid PID value'; return 1;; esac
    test "${#value}" -le 10 || { fail 'Oversized PID value'; return 1; }
    test -d "/proc/$value" || return 0
    test "$(readlink "/proc/$value/exe" 2>/dev/null || :)" = "$2" || { fail 'PID belongs to another executable'; return 1; }
    printf '%s\n' "$value"
}
snapshot()
{
    spid="$(owned "$starter_pid" "$starter")" || return 1
    cpid="$(owned "$charon_pid" "$charon")" || return 1
    for candidate in $(pidof starter charon 2>/dev/null || :); do
        test "$candidate" = "$spid" || test "$candidate" = "$cpid" || { fail 'Untracked IPsec process; refusing lifecycle action'; return 1; }
    done
}
validate()
{
    test -x "$ipsec" && test -x "$starter" && test -x "$charon" || { fail 'IPsec commands unavailable'; return 1; }
    test -f "$config" && test -r "$config" || { fail 'Existing ipsec.conf required'; return 1; }
    "$starter" --conftest --conf "$config"
}
start_service()
{
    snapshot || return 1
    test -z "$spid$cpid" || { fail 'IPsec already present; use restart'; return 1; }
    validate || return 1
    "$ipsec" start --conf "$config" || return 1
    attempts=0
    while test "$attempts" -lt 10; do
        snapshot || return 1
        test -z "$spid" || test -z "$cpid" || return 0
        sleep 1
        attempts=$((attempts + 1))
    done
    fail 'Startup not confirmed; inspect local IPsec logs'
}
stop_service()
{
    snapshot || return 1
    if test -z "$spid"; then
        test -z "$cpid" || { fail 'Orphan charon; refusing to signal unowned supervisor'; return 1; }
        return 0
    fi
    # Let starter stop its children; never use the upstream forced-kill fallback.
    kill -TERM "$spid" || return 1
    attempts=0
    while test "$attempts" -lt 10; do
        snapshot || return 1
        test -n "$spid$cpid" || return 0
        sleep 1
        attempts=$((attempts + 1))
    done
    fail 'Stop timed out; restart aborted'
}
test "$#" -eq 1 || exit 2
case "${1:-}" in
    status) snapshot || exit 1; test -n "$spid" && test -n "$cpid"; exit $?;;
    check) validate; exit $?;;
    start|stop|restart) ;;
    *) echo 'Usage: strongswan-service.sh {check|status|start|stop|restart}' >&2; exit 2;;
esac
exec 9>"$lock"
flock -x -n 9 || { fail 'Lifecycle action already active'; exit 1; }
case "$1" in
    start) start_service;;
    stop) stop_service;;
    restart) stop_service && start_service;;
esac
