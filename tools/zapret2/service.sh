#!/bin/sh
# Zapret2 service: explicit start/stop with a dedicated mangle chain.
# Factory-off. Requires a user strategy file and never starts by itself.
# Queue rules are fail-open: if nfqws2 disappears or wedges, traffic bypasses
# the queue instead of waiting indefinitely.

PATH=${ZAPRET2_PATH:-/opt/bin:/opt/sbin:/bin:/sbin:/usr/bin:/usr/sbin}
export PATH

NFQWS2=${ZAPRET2_NFQWS2:-/usr/sbin/nfqws2}
ARGS=${ZAPRET2_ARGS:-/etc/storage/zapret2.args}
STORAGE=$(dirname "$ARGS")
PRESETS=${ZAPRET2_PRESETS:-/usr/share/zapret2/presets}
PIDFILE=${ZAPRET2_PIDFILE:-/var/run/zapret2.pid}
LUA_DIR=${ZAPRET2_LUA_DIR:-/usr/share/zapret2}
CHAIN=ZAPRET2
QNUM=200
CLIENT_SET=wr_classic_zapret2_clients
IPSET_APPLY=${ZAPRET2_IPSET_APPLY:-/usr/sbin/wr-classic-ipset-apply}

client_mode() {
    mode=$(nvram get zapret2_clients_mode 2>/dev/null)
    case "$mode" in
        ''|exclude) echo exclude ;;
        include) echo include ;;
        *) return 1 ;;
    esac
}

wan_iface() {
    iface=$(nvram get zapret2_iface 2>/dev/null)
    [ -n "$iface" ] || iface=$(nvram get wan_ifname 2>/dev/null)
    [ -n "$iface" ] || iface=$(nvram get wan0_ifname 2>/dev/null)
    [ -n "$iface" ] || return 1
    [ ${#iface} -le 15 ] || return 1
    case "$iface" in
        *[!A-Za-z0-9_.:-]*) return 1 ;;
    esac
    [ -d "/sys/class/net/$iface" ] || return 1
    echo "$iface"
}

ipv4_exclusions() {
    file="$STORAGE/zapret2.$1-exclude"
    [ -e "$file" ] || return 0
    [ -f "$file" ] && [ -r "$file" ] || return 1
    size=$(wc -c <"$file") || return 1
    [ "$size" -le 4096 ] || return 1
    awk '
        { sub(/#.*/, ""); gsub(/^[[:space:]]+|[[:space:]]+$/, "") }
        !length { next }
        {
            if (++count > 64 || $0 !~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(\/[0-9]+)?$/)
                exit 1
            parts = split($0, ip, /[.\/]/)
            for (i = 1; i <= parts; i++) {
                if ((length(ip[i]) > 1 && substr(ip[i], 1, 1) == "0") ||
                    length(ip[i]) > 3 || ip[i] > (i == 5 ? 32 : 255))
                    exit 1
            }
            if (!seen[$0]++) print
        }
    ' "$file"
}

print_rules() {
    iface=$(wan_iface) || {
        echo "WAN interface is unavailable" >&2
        return 1
    }
    clients=$(ipv4_exclusions clients) || return 1
    mode=$(client_mode) || return 1
    destinations=$(ipv4_exclusions destinations) || return 1
    cat <<EOF
iptables -t mangle -N $CHAIN
iptables -t mangle -A $CHAIN -d 192.168.0.0/16 -j RETURN
iptables -t mangle -A $CHAIN -d 10.0.0.0/8 -j RETURN
iptables -t mangle -A $CHAIN -d 172.16.0.0/12 -j RETURN
iptables -t mangle -A $CHAIN -d 127.0.0.0/8 -j RETURN
EOF
    if [ "$mode" = include ]; then
        printf 'iptables -t mangle -A %s -m set ! --match-set %s src -j RETURN\n' "$CHAIN" "$CLIENT_SET"
    else
        for client in $clients; do
            printf 'iptables -t mangle -A %s -s %s -j RETURN\n' "$CHAIN" "$client"
        done
    fi
    for destination in $destinations; do
        printf 'iptables -t mangle -A %s -d %s -j RETURN\n' "$CHAIN" "$destination"
    done
    cat <<EOF
iptables -t mangle -A $CHAIN -p tcp -j NFQUEUE --queue-num $QNUM --queue-bypass
iptables -t mangle -A $CHAIN -p udp -j NFQUEUE --queue-num $QNUM --queue-bypass
iptables -t mangle -I POSTROUTING 1 -o $iface -j $CHAIN
EOF
}

chain_exists() {
    iptables -t mangle -n -L "$CHAIN" >/dev/null 2>&1
}

rules_installed() {
    mode=$(client_mode) || return 1
    if [ "$mode" = include ]; then
        iptables -t mangle -C "$CHAIN" -m set ! --match-set "$CLIENT_SET" src -j RETURN ||
            return 1
    fi
    iptables -t mangle -C POSTROUTING -o "$(wan_iface)" -j "$CHAIN" \
        >/dev/null 2>&1 || return 1
    iptables -t mangle -C "$CHAIN" -p tcp -j NFQUEUE \
        --queue-num "$QNUM" --queue-bypass >/dev/null 2>&1 || return 1
    iptables -t mangle -C "$CHAIN" -p udp -j NFQUEUE \
        --queue-num "$QNUM" --queue-bypass >/dev/null 2>&1
}

remove_rules() {
    hooks=$(iptables -t mangle -S POSTROUTING) || return 1
    interfaces=$(printf '%s\n' "$hooks" | sed -n 's/^-A POSTROUTING -o \([A-Za-z0-9_.:-]*\) -j ZAPRET2$/\1/p')
    for old_iface in $interfaces; do
        iptables -t mangle -D POSTROUTING -o "$old_iface" -j "$CHAIN" || return 1
    done
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
    clients=$(ipv4_exclusions clients) || return 1
    mode=$(client_mode) || return 1
    destinations=$(ipv4_exclusions destinations) || return 1
    iptables -t mangle -N "$CHAIN" || return 1
    iptables -t mangle -A "$CHAIN" -d 192.168.0.0/16 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 10.0.0.0/8 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 172.16.0.0/12 -j RETURN || return 1
    iptables -t mangle -A "$CHAIN" -d 127.0.0.0/8 -j RETURN || return 1
    if [ "$mode" = include ]; then
        iptables -t mangle -A "$CHAIN" -m set ! --match-set "$CLIENT_SET" src -j RETURN || return 1
    else
        for client in $clients; do
            iptables -t mangle -A "$CHAIN" -s "$client" -j RETURN || return 1
        done
    fi
    for destination in $destinations; do
        iptables -t mangle -A "$CHAIN" -d "$destination" -j RETURN || return 1
    done
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
    cmdline=$(cat "/proc/$pid/cmdline" 2>/dev/null | tr '\000' ' ') || return 1
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
    profile=$(nvram get zapret2_profile 2>/dev/null)
    case "$profile" in
        ''|0) ;;
        [1-9]|10) ARGS="$ARGS.$profile" ;;
        preset[5-9])
            ARGS="$PRESETS/strategy${profile#preset}"
            [ -s "$STORAGE/zapret2.hosts" ] ||
                { echo "Built-in strategy requires a domain list" >&2; return 1; }
            ;;
        *) echo "Invalid strategy profile" >&2; return 1 ;;
    esac
    [ -s "$ARGS" ] || { echo "strategy file $ARGS is required"; return 1; }
    args_size=$(wc -c <"$ARGS" 2>/dev/null) || {
        echo "strategy file size is unavailable"
        return 1
    }
    case "$args_size" in
        *[!0-9]*) echo "strategy file size is invalid"; return 1 ;;
    esac
    [ "$args_size" -le 8192 ] || {
        echo "strategy file exceeds 8192 bytes"
        return 1
    }
    for script in zapret-lib.lua zapret-antidpi.lua zapret-auto.lua; do
        [ -r "$LUA_DIR/$script" ] || {
            echo "Zapret2 Lua support file is missing: $LUA_DIR/$script"
            return 1
        }
    done
    wan_iface >/dev/null || { echo "WAN interface is unavailable"; return 1; }
    mode=$(client_mode) || { echo "Invalid IPv4 client mode" >&2; return 1; }
    clients=$(ipv4_exclusions clients) || { echo "Invalid IPv4 client list" >&2; return 1; }
    if [ "$mode" = include ]; then
        [ -x "$IPSET_APPLY" ] && [ -n "$clients" ] ||
            { echo "Selected-client mode requires IPSet and at least one client" >&2; return 1; }
        WR_CLASSIC_IPSET_REQUIRE_ENTRIES=1 "$IPSET_APPLY"             "$STORAGE/zapret2.clients-exclude" zapret2_clients || return 1
    fi
    ipv4_exclusions destinations >/dev/null || { echo "Invalid IPv4 destination exclusion list" >&2; return 1; }

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

    set -f
    # The strategy file is a root-managed list of nfqws2 arguments.
    set -- $(cat "$ARGS")
    set +f
    [ "$#" -gt 0 ] || {
        remove_rules
        echo "strategy file contains no arguments"
        return 1
    }

    domains="$STORAGE/zapret2.hosts"
    domain_exclusions="$STORAGE/zapret2.hosts-exclude"
    for list in "$domains" "$domain_exclusions"; do
        if [ -e "$list" ] && { [ ! -f "$list" ] || [ "$(wc -c <"$list")" -gt 8192 ]; }; then
            remove_rules
            echo "Invalid Zapret2 domain list" >&2
            return 1
        fi
    done
    first=1
    for option do
        shift
        case "$option" in
            --new|--new=*) set -- "$@" "$option"; add_lists=1 ;;
            *) add_lists=$first ;;
        esac
        if [ "$add_lists" = 1 ]; then
            if [ -s "$domains" ]; then
                set -- "$@" "--hostlist=$domains"
            fi
            if [ -s "$domain_exclusions" ]; then
                set -- "$@" "--hostlist-exclude=$domain_exclusions"
            fi
        fi
        case "$option" in --new|--new=*) ;; *) set -- "$@" "$option" ;; esac
        first=0
    done
    if [ "$(nvram get zapret2_log 2>/dev/null)" = 1 ]; then
        set -- "$@" --debug=syslog
    fi
    "$NFQWS2" --qnum="$QNUM" \
        --lua-init="@$LUA_DIR/zapret-lib.lua" \
        --lua-init="@$LUA_DIR/zapret-antidpi.lua" \
        --lua-init="@$LUA_DIR/zapret-auto.lua" \
        "$@" </dev/null >/dev/null 2>&1 &
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
