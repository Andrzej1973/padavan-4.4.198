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
dns_dir=${WRVPN_DNS_DIR:-/var/run}
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

active_ids()
{
    for dir in "$run_dir"/*; do
        test -d "$dir" || continue
        id=${dir##*/}
        case "$id" in ''|*[!0-9]*) continue;; esac
        echo "$id"
    done
}

acquire()
{
	type flock >/dev/null 2>&1 || { fail 'flock is required'; return 1; }
	exec 9>"$lock"
	flock -x -n 9 || { fail 'another run holds the lock'; return 1; }
}

acquire_wait()
{
	type flock >/dev/null 2>&1 || { fail 'flock is required'; return 1; }
	exec 9>"$lock"
	flock -x 9 || { fail 'unable to acquire the lifecycle lock'; return 1; }
}

dns_sync()
{
    mkdir -p "$dns_dir" || { fail 'DNS directory unavailable'; return 1; }
    test -d "$dns_dir" && test ! -L "$dns_dir" || { fail 'Invalid DNS directory'; return 1; }
    test ! -L "$run_dir" || { fail 'VPN runtime directory is a symlink'; return 1; }
    tmp=$(mktemp "$dns_servers.XXXXXX") || { fail 'DNS temporary file unavailable'; return 1; }
    if test "$(nvram get wrvpn_use_dns 2>/dev/null || :)" = "1"; then
        for file in "$run_dir"/*/wrv*.dns; do
            test -f "$file" || continue
            if test -L "$file"; then rm -f "$tmp"; fail 'VPN DNS entry is a symlink'; return 1; fi
            while IFS= read -r server; do
                case "$server" in ''|*[!0-9a-fA-F:.]*) continue;; esac
                printf 'server=%s\n' "$server" >> "$tmp" || { rm -f "$tmp"; fail 'DNS list write failed'; return 1; }
            done < "$file"
        done
    fi
    # The daemon may read the server addresses after dropping privileges.
    chmod 0644 "$tmp" && mv -f "$tmp" "$dns_servers" || {
        rm -f "$tmp"; fail 'DNS file update failed'; return 1;
    }
    killall -HUP dnsmasq 2>/dev/null || :
}

sync_dns_service()
{
    acquire_wait || return 1
    dns_sync
}

start_service()
{
    acquire || return 1
    guard=$(protect)
    result=0
    for id in $(ids); do
        case "$id" in ''|*[!0-9]*) fail "invalid profile id: $id" || result=1; break;; esac
        "$ctl" up "$id" "$guard" || {
            fail "profile $id failed to start" || result=1
            break
        }
    done
    dns_sync || result=1
    return "$result"
}

stop_service()
{
    acquire || return 1
    result=0
    seen=" "
    # Enabled ids and any id that still has a runtime directory: removing an id
    # from nvram must not leave its owned link running until the next reboot.
    for id in $(ids) $(active_ids); do
        case "$id" in ''|*[!0-9]*) continue;; esac
        case "$seen" in *" $id "*) continue;; esac
        seen="$seen$id "
        if "$ctl" down "$id"; then
            :
        else
            rc=$?
            case $rc in
                5) :;;  # no stored profile left; nothing this call can release
                *) fail "profile $id failed to stop" || result=1;;
            esac
        fi
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
    dns-sync) sync_dns_service;;
    *) echo "usage: $0 start|stop|status" >&2; exit 2;;
esac
