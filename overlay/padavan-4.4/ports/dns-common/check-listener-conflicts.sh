#!/bin/sh
set -eu
WR_DOH_BINARY=${WR_DOH_BINARY:-$(command -v sh)}
WR_STUBBY_BINARY=${WR_STUBBY_BINARY:-$(command -v sh)}
guard=${1:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/dns-listener-guard.sh}
. "$guard"

stubby_enable=1 stubby_listen_port=5453 stubby_listen_mode=0
doh_enable=1 doh_listen_port=5452 doh_listen_mode=0
doh_server0=https://dns.google/dns-query doh_server1=https://cloudflare-dns.com/dns-query
doh_server2= doh_server3= lan_ipaddr_t=192.168.1.1
nvram()
{
    [ "$1" = get ] || return 1
    case "$2" in
        stubby_enable) printf '%s\n' "$stubby_enable";;
        stubby_listen_port) printf '%s\n' "$stubby_listen_port";;
        stubby_listen_mode) printf '%s\n' "$stubby_listen_mode";;
        doh_enable) printf '%s\n' "$doh_enable";;
        doh_listen_port) printf '%s\n' "$doh_listen_port";;
        doh_listen_mode) printf '%s\n' "$doh_listen_mode";;
        doh_server0) printf '%s\n' "$doh_server0";;
        doh_server1) printf '%s\n' "$doh_server1";;
        doh_server2) printf '%s\n' "$doh_server2";;
        doh_server3) printf '%s\n' "$doh_server3";;
        lan_ipaddr_t) printf '%s\n' "$lan_ipaddr_t";;
        *) return 1;;
    esac
}

# Host fixture defaults to an existing executable so it can model both
# packages without creating files. Target QEMU passes the actual ROMFS paths.
fixture_doh_binary=$WR_DOH_BINARY
fixture_stubby_binary=$WR_STUBBY_BINARY

expect_conflict()
{
    description=$1 service=$2 address=$3 port=$4
    if wr_dns_listener_conflict "$service" "$address" "$port" 2>/dev/null; then
        echo "FAIL expected listener conflict: $description" >&2
        exit 1
    fi
    echo "PASS refuses listener conflict: $description"
}
expect_clear()
{
    description=$1 service=$2 address=$3 port=$4
    if ! wr_dns_listener_conflict "$service" "$address" "$port"; then
        echo "FAIL unexpected listener conflict: $description" >&2
        exit 1
    fi
    echo "PASS permits non-conflicting listeners: $description"
}

doh_listen_port=5453
expect_conflict 'same loopback address and port' stubby 127.0.0.1 5453
WR_DOH_BINARY=/missing/https_dns_proxy
expect_clear 'stale DoH enable flag without its image binary' stubby 127.0.0.1 5453
WR_DOH_BINARY=$fixture_doh_binary
doh_listen_port=5452
doh_server1=https://cloudflare-dns.com/dns-query
expect_conflict 'second DoH resolver overlaps Stubby' doh 127.0.0.1 5452
doh_listen_port=5453
doh_server1=
doh_listen_mode=1
expect_clear 'same port on distinct specific addresses' stubby 127.0.0.1 5453
doh_listen_mode=2
expect_conflict 'wildcard DoH overlaps loopback Stubby' stubby 127.0.0.1 5453
doh_listen_mode=99
expect_conflict 'invalid enabled DoH bind mode fails closed' stubby 127.0.0.1 5453
doh_listen_mode=0
doh_listen_port=bad
expect_conflict 'invalid enabled DoH port fails closed' stubby 127.0.0.1 5453
doh_listen_port=65533
expect_conflict 'out-of-range enabled DoH port fails closed' stubby 127.0.0.1 5453
doh_listen_port=5053
expect_clear 'default listener ranges' stubby 127.0.0.1 5453
doh_enable=0
doh_listen_port=5453
expect_clear 'disabled DoH does not reserve a port' stubby 127.0.0.1 5453
doh_enable=1
stubby_listen_mode=1
expect_clear 'different specific addresses do not conflict from DoH side' doh 127.0.0.1 5453
stubby_listen_mode=99
expect_conflict 'invalid enabled Stubby bind mode fails closed' doh 127.0.0.1 5453
stubby_listen_mode=0
stubby_listen_port=bad
expect_conflict 'invalid enabled Stubby port fails closed' doh 127.0.0.1 5453
stubby_listen_port=65536
expect_conflict 'out-of-range enabled Stubby port fails closed' doh 127.0.0.1 5453
stubby_listen_port=53
expect_conflict 'system-port enabled Stubby fails closed' doh 127.0.0.1 5453
stubby_listen_port=5453
WR_STUBBY_BINARY=/missing/stubby
expect_clear 'stale Stubby enable flag without its image binary' doh 127.0.0.1 5453
WR_STUBBY_BINARY=$fixture_stubby_binary
expect_conflict 'DoH start checks an enabled Stubby listener' doh 127.0.0.1 5453
echo 'PASS DNS listener-conflict fixture'
