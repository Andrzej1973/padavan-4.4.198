#!/bin/sh
# Candidate helper; integration and target runtime checks are still required.
STUBBY_BIN=/usr/sbin/stubby
STUBBY_CONFIG=/etc/storage/stubby/stubby.yml
PID_FILE=/var/run/stubby.pid

fail() { logger -t stubby "$*"; echo "$*" >&2; exit 1; }

valid_ipv4()
{
    printf '%s\n' "$1" | awk -F. '
        NF != 4 { exit 1 }
        { for (i=1; i<=4; i++) if ($i !~ /^[0-9]+$/ || length($i)>3 || $i+0>255) exit 1 }
    '
}

valid_address()
{
    case "$1" in
        *:*)
            # The target parser performs the final IPv6 syntax check.
            case "$1" in *[!0-9a-fA-F:.]*) return 1;; esac
            [ "${#1}" -le 45 ]
            ;;
        *) valid_ipv4 "$1";;
    esac
}

running()
{
    [ -f "$PID_FILE" ] || return 1
    service_pid=$(cat "$PID_FILE")
    case "$service_pid" in ''|*[!0-9]*) return 1;; esac
    [ "$service_pid" -gt 1 ] || return 1
    [ "$(cat "/proc/$service_pid/comm" 2>/dev/null)" = stubby ] &&
        kill -0 "$service_pid" 2>/dev/null
}

make_config()
{
    port=$(nvram get stubby_listen_port)
    case "$port" in ''|*[!0-9]*) fail 'Invalid Stubby listen port';; esac
    [ "${#port}" -le 5 ] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ] ||
        fail 'Stubby listen port must be between 1 and 65535'
    round_robin=$(nvram get stubby_round_robin)
    case "$round_robin" in 0|1) ;; *) fail 'Invalid Stubby round-robin setting';; esac
    listen_mode=$(nvram get stubby_listen_mode)
    case "$listen_mode" in
        0) listen_address=127.0.0.1;;
        1) listen_address=$(nvram get lan_ipaddr_t); valid_ipv4 "$listen_address" || fail 'Invalid LAN listen address';;
        2) listen_address=0.0.0.0;;
        *) fail 'Invalid Stubby listen mode';;
    esac
    mode=$(nvram get stubby_mode)
    case "$mode" in
        0|1) auth=GETDNS_AUTHENTICATION_REQUIRED;;
        2|3) auth=GETDNS_AUTHENTICATION_NONE;;
        *) fail 'Invalid Stubby privacy mode';;
    esac
    mkdir -p /etc/storage/stubby || fail 'Cannot create Stubby configuration directory'
    config_tmp_dir=$(mktemp -d /etc/storage/stubby/.stubby.XXXXXX) || fail 'Cannot create temporary configuration directory'
    config_tmp="$config_tmp_dir/stubby.yml"
    trap 'rm -f "$config_tmp"; rmdir "$config_tmp_dir"' EXIT
    trap 'exit 1' HUP INT TERM
    {
        printf '%s\n' 'resolution_type: GETDNS_RESOLUTION_STUB' \
            'tls_query_padding_blocksize: 128' 'edns_client_subnet_private: 1' 'idle_timeout: 10000'
        printf 'round_robin_upstreams: %s\ntls_authentication: %s\n' "$round_robin" "$auth"
        printf '%s\n' 'dns_transport_list:' '  - GETDNS_TRANSPORT_TLS'
        case "$mode" in 2|3) printf '%s\n' '  - GETDNS_TRANSPORT_UDP' '  - GETDNS_TRANSPORT_TCP';; esac
        printf 'listen_addresses:\n  - "%s@%s"\nupstream_recursive_servers:\n' "$listen_address" "$port"
    } > "$config_tmp" || fail 'Cannot write Stubby configuration'
    resolver_count=0
    for i in 0 1 2 3; do
        server=$(nvram get "stubby_server$i")
        address=$(nvram get "stubby_server_ip$i")
        [ -n "$server$address" ] || continue
        [ -n "$server" ] && [ -n "$address" ] || fail "Incomplete Stubby resolver $i"
        case "$server" in *[!a-zA-Z0-9.-]*|.*|-*) fail "Invalid TLS authentication name for resolver $i";; esac
        [ "${#server}" -le 253 ] || fail "TLS authentication name too long for resolver $i"
        valid_address "$address" || fail "Invalid address for resolver $i"
        printf '  - address_data: "%s"\n    tls_auth_name: "%s"\n' "$address" "$server" >> "$config_tmp" ||
            fail 'Cannot write Stubby resolver'
        resolver_count=$((resolver_count + 1))
    done
    [ "$resolver_count" -gt 0 ] || fail 'No Stubby resolvers configured'
    "$STUBBY_BIN" -C "$config_tmp" -i >/dev/null || fail 'Stubby rejected the generated configuration'
    chmod 600 "$config_tmp" && mv -f "$config_tmp" "$STUBBY_CONFIG" ||
        fail 'Cannot install validated Stubby configuration'
    rmdir "$config_tmp_dir" || fail 'Cannot remove temporary configuration directory'
    trap - EXIT HUP INT TERM
}

start_service()
{
    [ -x "$STUBBY_BIN" ] || fail 'Stubby executable missing'
    running && return 0
    # Refuse a second instance even if its PID file was lost.
    pidof stubby >/dev/null && fail 'Stubby process exists without a verified PID file'
    rm -f "$PID_FILE"
    make_config
    # Do not let the forked daemon retain the lifecycle lock descriptor.
    "$STUBBY_BIN" -C "$STUBBY_CONFIG" -g 9>&- || fail 'Stubby startup failed'
    sleep 1
    running || fail 'Stubby did not remain running'
    logger -t stubby "Started on $listen_address:$port"
}

stop_service()
{
    if ! running; then
        pidof stubby >/dev/null && fail 'Cannot safely identify the existing Stubby process'
        rm -f "$PID_FILE"
        return 0
    fi
    kill -TERM "$service_pid" || fail 'Cannot stop Stubby'
    tries=0
    while running; do
        [ "$tries" -lt 10 ] || fail 'Stubby did not stop; refusing to start a second instance'
        sleep 1
        tries=$((tries + 1))
    done
    rm -f "$PID_FILE"
    logger -t stubby 'Stopped'
}

# One lock covers the entire restart, including stop and configuration validation.
# /var/run is volatile; reboot cannot leave a held lock behind.
case "$1" in
    start|stop|restart) ;;
    *) echo "Usage: $0 {start|stop|restart}" >&2; exit 1;;
esac
command -v flock >/dev/null || fail 'Required lifecycle locking utility missing'
exec 9>/var/run/stubby-service.lock || fail 'Cannot open Stubby lifecycle lock'
flock -x -n 9 || fail 'Another Stubby lifecycle operation is in progress'

case "$1" in
    start) start_service;;
    stop) stop_service;;
    restart) stop_service && start_service;;
    *) echo "Usage: $0 {start|stop|restart}" >&2; exit 1;;
esac
