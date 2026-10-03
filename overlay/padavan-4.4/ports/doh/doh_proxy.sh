#!/bin/sh
# Foreground children retain verified PID ownership; defaults keep DoH disabled.
set -eu
binary=/usr/sbin/https_dns_proxy
piddir=/var/run/doh-proxy
ca=/usr/share/doh-proxy/cacert.pem

fail() { logger -t DoH "$*"; return 1; }
owned_pid()
{
    test -f "$1" || return 1
    pid="$(cat "$1")"
    case "$pid" in ''|*[!0-9]*|0|1) return 1;; esac
    test "$(readlink "/proc/$pid/exe" 2>/dev/null || :)" = "$binary" || return 1
    kill -0 "$pid" 2>/dev/null
}
stop_service()
{
    for index in 0 1 2 3; do
        file="$piddir/$index.pid"
        if owned_pid "$file"; then
            kill "$pid"
            attempts=0
            while owned_pid "$file"; do
                attempts=$((attempts + 1))
                test "$attempts" -lt 10 || { fail 'Stop timed out'; return 1; }
                sleep 1
            done
        fi
        rm -f "$file"
    done
}
start_service()
{
    test -x "$binary" && test -r "$ca"
    port="$(nvram get doh_listen_port)"
    case "$port" in ''|*[!0-9]*) fail 'Invalid listener port'; return 1;; esac
    test "${#port}" -le 5 && test "$port" -ge 1 && test "$port" -le 65532 || { fail 'Listener port must be 1..65532'; return 1; }
    port="$(printf '%s\n' "$port" | awk '{printf "%d", $0+0}')"
    address=127.0.0.1
    case "$(nvram get doh_listen_mode)" in
        0) ;;
        1) address="$(nvram get lan_ipaddr_t)";;
        2) address=0.0.0.0;;
        *) fail 'Invalid listener mode'; return 1;;
    esac
    printf '%s\n' "$address" | awk -F. 'NF!=4 {exit 1} {for(i=1;i<=4;i++) if($i!~/^[0-9]+$/ || $i>255) exit 1}' || { fail 'Invalid listener address'; return 1; }
    bootstrap="$(nvram get doh_bootstrap_dns)"
    quic="$(nvram get doh_quic)"
    case "$quic" in 0|1) ;; *) fail 'Invalid HTTP/3 mode'; return 1;; esac
    # Validate all profiles before starting any child.
    count=0
    for index in 0 1 2 3; do
        url="$(nvram get doh_server$index)"
        test -n "$url" || continue
        case "$url" in https://?*) ;; *) fail 'Resolver requires HTTPS'; return 1;; esac
        test "${#url}" -le 1024 || { fail 'Resolver URL is too long'; return 1; }
        count=$((count + 1))
    done
    test "$count" -gt 0 || { fail 'No resolver configured'; return 1; }
    for index in 0 1 2 3; do
        if owned_pid "$piddir/$index.pid"; then
            fail 'Already running; use restart to apply settings'; return 1
        fi
    done
    if pidof https_dns_proxy >/dev/null 2>&1; then
        fail 'An untracked DoH process is already running'; return 1
    fi
    mkdir -p "$piddir"
    for index in 0 1 2 3; do
        url="$(nvram get doh_server$index)"
        test -n "$url" || continue
        set -- -a "$address" -p "$((port + index))" -r "$url" -C "$ca" -u nobody -g nogroup -4
        test -z "$bootstrap" || set -- "$@" -b "$bootstrap"
        test "$quic" != 1 || set -- "$@" -q
        "$binary" "$@" -l "$piddir/$index.log" 9>&- &
        printf '%s\n' "$!" > "$piddir/$index.pid"
    done
    sleep 1
    for index in 0 1 2 3; do
        url="$(nvram get doh_server$index)"
        test -n "$url" || continue
        if ! owned_pid "$piddir/$index.pid"; then
            stop_service || :
            fail 'Resolver startup failed; inspect local DoH logs'; return 1
        fi
    done
    logger -t DoH 'Started configured HTTPS resolvers'
}
case "${1:-}" in start|stop|restart) ;; *) echo 'Usage: doh_proxy.sh {start|stop|restart}' >&2; exit 1;; esac
exec 9>/var/run/doh-proxy.lock
flock -x -n 9 || { fail 'Another DoH operation is in progress'; exit 1; }
case "$1" in
    start) start_service;;
    stop) stop_service;;
    restart) stop_service; start_service;;
esac
