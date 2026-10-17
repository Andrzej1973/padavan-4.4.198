#!/bin/sh
# Independent VPN profiles: default-off start/stop driven by nvram.
#   wrvpn_enabled - comma-separated profile ids to bring up
#   wrvpn_protect - comma-separated prefixes that must never enter a tunnel
# With wrvpn_protect empty the controller refuses profile addresses, so a
# misconfigured service cannot pull the router's own network into a tunnel.
set -eu
umask 077
ctl=${WRVPN_CTL:-/usr/sbin/wr-vpn-profile}
lock=${WRVPN_LOCK:-/var/run/wr-vpn-profiles.lock}
tag=wr-vpn-profiles
dns_dir=${WRVPN_DNS_DIR:-/etc/storage/dnsmasq}
run_dir=${WRVPN_RUN_DIR:-/var/run/wrvpn}
dns_servers=$dns_dir/wrvpn.servers

fail()
{
    logger -t "$tag" "$*" 2>/dev/null || :
    echo "$*" >&2
    return 1
}

ids()
{
    nvram get wrvpn_enabled 2>/dev/null | tr ',' ' ' | tr -s ' '
}

protect()
{
    nvram get wrvpn_protect 2>/dev/null || :
}

acquire()
{
    if command -v flock >/dev/null 2>&1; then
        exec 9>"$lock"
        flock -n 9 || { fail 'another run holds the lock'; return 1; }
    fi
}

dns_sync()
{
    if test "$(nvram get wrvpn_use_dns 2>/dev/null || :)" = "1"; then
        tmp=$dns_servers.tmp
        mkdir -p "$dns_dir" 2>/dev/null || :
        : > "$tmp"
        for file in "$run_dir"/*/wrv*.dns; do
            test -f "$file" || continue
            while IFS= read -r server; do
                case "$server" in ''|*[!0-9a-fA-F:.]*) continue;; esac
                echo "server=$server" >> "$tmp"
            done < "$file"
        done
        mv "$tmp" "$dns_servers" || { fail 'DNS file update failed'; return 1; }
    else
        rm -f "$dns_servers"
    fi
    killall -HUP dnsmasq 2>/dev/null || :
}

start_service()
{
    acquire || return 1
    guard=$(protect)
    for id in $(ids); do
        case "$id" in ''|*[!0-9]*) fail "invalid profile id: $id"; return 1;; esac
        "$ctl" up "$id" "$guard" || { fail "profile $id failed to start"; return 1; }
    done
    dns_sync
}

stop_service()
{
    acquire || return 1
    result=0
    for id in $(ids); do
        case "$id" in ''|*[!0-9]*) continue;; esac
        "$ctl" down "$id" || { fail "profile $id failed to stop"; result=1; }
    done
    dns_sync || result=1
    return $result
}

status_service()
{
    for id in $(ids); do
        case "$id" in ''|*[!0-9]*) continue;; esac
        "$ctl" plan "$id" || :
    done
}

case "${1:-}" in
    start) start_service;;
    stop) stop_service;;
    status) status_service;;
    *) echo "usage: $0 start|stop|status" >&2; exit 2;;
esac
