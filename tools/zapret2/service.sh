#!/bin/sh
# Zapret2 service: explicit start/stop with a dedicated mangle chain.
# Factory-off. Requires a user strategy file and never starts by itself.
# Queue rules are fail-open: if nfqws2 disappears or wedges, traffic bypasses
# the queue instead of waiting indefinitely.

PATH=${ZAPRET2_PATH:-/opt/bin:/opt/sbin:/bin:/sbin:/usr/bin:/usr/sbin}
export PATH

NFQWS2=${ZAPRET2_NFQWS2:-/usr/sbin/nfqws2}
ARGS=${ZAPRET2_ARGS:-/etc/storage/zapret2.args}
PIDFILE=${ZAPRET2_PIDFILE:-/var/run/zapret2.pid}
CHAIN=ZAPRET2
QNUM=200

wan_iface() {
    iface=$(nvram get wan_ifname 2>/dev/null)
    [ -n "$iface" ] || iface=$(nvram get wan0_ifname 2>/dev/null)
    [ -n "$iface" ] || return 1
    [ ${#iface} -le 15 ] || return 1
    case "$iface" in
        *[!A-Za-z0-9_.:-]*) return 1 ;;
    esac
    echo "$iface"
}

print_rules() {
    iface=$(wan_iface) || {
        echo "WAN interface is unavailable" >&2
        return 1
    }
    cat <<EOF
iptables -t mangle -N $CHAIN
iptables -t mangle -A $CHAIN -d 192.168.0.0/16 -j RETURN
iptables -t mangle -A $CHAIN -d 10.0.0.0/8 -j RETURN
iptables -t mangle -A $CHAIN -d 172.16.0.0/12 -j RETURN
iptables -t mangle -A $CHAIN -d 127.0.0.0/8 -j RETURN
iptables -t mangle -A $CHAIN -p tcp -j NFQUEUE --queue-num $QNUM --queue-bypass
iptables -t mangle -A $CHAIN -p udp -j NFQUEUE --queue-num $QNUM --queue-bypass
iptables -t mangle -I POSTROUTING 1 -o $iface -j $CHAIN
EOF
}

chain_exists() {
    iptables -t mangle -n -L "$CHAIN" >/dev/null 2>&1
}

rules_installed() {
    iptables -t mangle -C POSTROUTING -o "$(wan_iface)" -j "$CHAIN" \
        >/dev/null 2>&1 || return 1
    iptables -t mangle -C "$CHAIN" -p tcp -j NFQUEUE \
        --queue-num "$QNUM" --queue-bypass >/dev/null 2>&1 || return 1
    iptables -t mangle -C "$CHAIN" -p udp -j NFQUEUE \
        --queue-num "$QNUM" --queue-bypass >/dev/null 2>&1
}

remove_rules() {
    iface=$(wan_iface 2>/dev/null)
    if [ -n "$iface" ]; then
        while iptables -t mangle -D POSTROUTING -o "$iface" -j "$CHAIN" \
            2>/dev/null; do :; done
    fi
    while iptables -t mangle -D POSTROUTING -j "$CHAIN" 2>/dev/null; do :; done
    if chain_exists; then
        iptables -t mangle -F "$CHAIN" || return 1
        iptables -t mangle -X "$CHAIN" || return 1
    fi
    return 0
}

install_rules() {
    iface=$(wan_iface) || {
        echo "WAN interface is unavailable" >&2
        return 1
    }
    iptables -t mangle -N "$CHAIN" || return 1
    iptables -t mangle -A "$CHAIN" -d 192.168.0.0/16 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 10.0.0.0/8 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 172.16.0.0/12 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 127.0.0.0/8 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -p tcp \
        -j NFQUEUE --queue-num "$QNUM" --queue-bypass || return 1
    iptables -t mangle -A "$CHAIN" -p udp \
        -j NFQUEUE --queue-num "$QNUM" --queue-bypass || return 1
    iptables -t mangle -I POSTROUTING 1 -o "$iface" -j "$CHAIN" || return 1
}

pid_owns_nfqws2() {
    pid=$1
    [ -n "$pid" ] || return 1
    case "$pid" in
        *[!0-9]*) return 1 ;;
    esac
    [ -r "/proc/$pid/cmdline" ] || return 1
    cmdline=$(tr '\000' ' ' <"/proc/$pid/cmdline" 2>/dev/null) || return 1
    case " $cmdline " in
        *" $NFQWS2 "*) return 0 ;;
    esac
    return 1
}

processes() {
    [ -d /proc ] || return 1
    found=1
    for proc in /proc/[0-9]*; do
        pid=${proc##*/}
        if pid_owns_nfqws2 "$pid"; then
            echo "$pid"
            found=0
        fi
    done
    return "$found"
}

write_pidfile() {
    pid=$1
    tmp="$PIDFILE.$$"
    (umask 077 && echo "$pid" >"$tmp") && mv "$tmp" "$PIDFILE"
}

stop_processes() {
    pids=$(processes) || pids=
    if [ -n "$pids" ]; then
        for pid in $pids; do
            kill "$pid" 2>/dev/null
        done
        n=0
        while [ -n "$(processes)" ] && [ "$n" -lt 10 ]; do
            sleep 1
            n=$((n + 1))
        done
        pids=$(processes) || pids=
        if [ -n "$pids" ]; then
            for pid in $pids; do
                kill -9 "$pid" 2>/dev/null
            done
            n=0
            while [ -n "$(processes)" ] && [ "$n" -lt 5 ]; do
                sleep 1
                n=$((n + 1))
            done
        fi
    fi
    [ -z "$(processes)" ]
}

start() {
    [ -x "$NFQWS2" ] || { echo "nfqws2 is not installed"; return 1; }
    [ -s "$ARGS" ] || { echo "strategy file $ARGS is required"; return 1; }
    wan_iface >/dev/null || { echo "WAN interface is unavailable"; return 1; }

    pids=$(processes) || pids=
    if [ -n "$pids" ]; then
        instances=$(printf '%s\n' "$pids" | sed -n '$=')
    else
        instances=0
    fi
    if [ "$instances" -eq 1 ] && rules_installed; then
        pid=$(printf '%s\n' "$pids" | sed -n '1p')
        write_pidfile "$pid" || return 1
        echo "already running"
        return 0
    fi

    if [ -n "$pids" ]; then
        stop_processes || {
            echo "existing nfqws2 process could not be stopped"
            return 1
        }
    fi

    rm -f "$PIDFILE"
    remove_rules || return 1
    install_rules || {
        remove_rules
        echo "could not install NFQUEUE rules"
        return 1
    }

    old_ifs=$IFS
    set -f
    IFS=' '
    # The strategy file is a root-managed list of nfqws2 arguments.
    set -- $(cat "$ARGS")
    IFS=$old_ifs
    set +f
    [ "$#" -gt 0 ] || {
        remove_rules
        echo "strategy file contains no arguments"
        return 1
    }

    "$NFQWS2" --qnum="$QNUM" "$@" </dev/null >/dev/null 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    if pid_owns_nfqws2 "$(cat "$PIDFILE" 2>/dev/null)" && rules_installed; then
        echo "started"
    else
        stop_processes
        remove_rules || true
        rm -f "$PIDFILE"
        echo "nfqws2 failed to start"
        return 1
    fi
}

stop() {
    stop_processes
    process_result=$?
    rm -f "$PIDFILE"
    remove_rules || {
        echo "rules removal unverified"
        return 1
    }
    [ "$process_result" -eq 0 ] || {
        echo "nfqws2 process could not be stopped"
        return 1
    }
    echo "stopped"
}

status() {
    pids=$(processes) || pids=
    if [ ! -d /proc ]; then
        echo "process=unknown"
    elif [ -n "$pids" ]; then
        echo "process=running"
    else
        echo "process=stopped"
    fi
    if rules_installed; then
        echo "rules=installed"
    elif wan_iface >/dev/null; then
        echo "rules=absent"
    else
        echo "rules=unknown"
    fi
}

case "${1:-}" in
    start) start ;;
    stop) stop ;;
    restart) stop && start ;;
    status) status ;;
    rules) print_rules ;;
    *) echo "Usage: $0 start|stop|restart|status|rules"; exit 2 ;;
esac
