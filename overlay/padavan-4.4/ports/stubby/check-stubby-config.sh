#!/bin/sh
# Run the shipped stubby.sh configuration generator against stubbed router
# commands. Covers accepted settings, every rejection path and retention of
# the previous configuration on failure.
#
#   check-stubby-config.sh              run the fixture cases
#   check-stubby-config.sh DUMP         check one router's settings, where DUMP is
#                                       the output of: nvram show | grep -E '^(stubby_|lan_ipaddr_t=)'
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$here/stubby-test-env.sh"

failures=0
DEFAULTS='stubby_server0=dns.google
stubby_server_ip0=8.8.8.8
stubby_listen_port=5453
stubby_listen_mode=0
stubby_round_robin=1
stubby_mode=1
lan_ipaddr_t=192.168.1.1'

fail_case() { echo "FAIL $1: $2"; [ -n "$messages" ] && printf '  %s\n' "$messages"; failures=$((failures + 1)); }

no_leftovers()
{
    set -- "$work"/storage/stubby/.stubby.*
    [ ! -e "$1" ]
}

accepts()
{
    name=$1; shift
    generate "$@"
    if [ "$status" -ne 0 ]; then fail_case "$name" 'configuration rejected'; return 1; fi
    if ! cmp -s "$config" "$work/checked.yml"; then fail_case "$name" 'installed file differs from the file stubby validated'; return 1; fi
    if ! no_leftovers; then fail_case "$name" 'temporary directory left behind'; return 1; fi
    return 0
}

has() { grep -qxF -- "$2" "$config" || fail_case "$1" "missing line: $2"; }
count() { [ "$(grep -c -- "$2" "$config")" -eq "$3" ] || fail_case "$1" "expected $3 lines matching $2"; }

rejects()
{
    name=$1 reason=$2; shift 2
    mkdir -p "$work/storage/stubby"
    echo 'previous: working' > "$work/storage/stubby/stubby.yml"
    generate "$@"
    if [ "$status" -eq 0 ]; then fail_case "$name" 'invalid configuration accepted'; return; fi
    case "$messages" in *"$reason"*) ;; *) fail_case "$name" "expected reason: $reason";; esac
    [ "$(cat "$work/storage/stubby/stubby.yml")" = 'previous: working' ] ||
        fail_case "$name" 'previous configuration was not retained'
    no_leftovers || fail_case "$name" 'temporary directory left behind'
}

if [ $# -eq 1 ]; then
    [ -r "$1" ] || { echo "Cannot read $1"; exit 1; }
    generate "$(tr -d '\r' < "$1")"
    if [ "$status" -eq 0 ]; then
        echo 'ACCEPTED: stubby.sh generates this configuration:'
        cat "$config"
        exit 0
    fi
    echo 'REJECTED: stubby.sh refuses to start Stubby with these settings:'
    printf '  %s\n' "$messages"
    exit 1
fi

if accepts defaults "$DEFAULTS"; then
    has defaults '  - "127.0.0.1@5453"'
    has defaults 'tls_authentication: GETDNS_AUTHENTICATION_REQUIRED'
    has defaults 'round_robin_upstreams: 1'
    has defaults '  - address_data: "8.8.8.8"'
    has defaults '    tls_auth_name: "dns.google"'
    count defaults 'GETDNS_TRANSPORT_' 1
    count defaults 'address_data:' 1
fi

FOUR='stubby_server0=dns.quad9.net
stubby_server_ip0=9.9.9.9
stubby_server1=one.one.one.one
stubby_server_ip1=1.1.1.1
stubby_server2=dns.google
stubby_server_ip2=2001:4860:4860::8888
stubby_server3=dns.adguard-dns.com
stubby_server_ip3=94.140.14.14
stubby_listen_port=5453
stubby_listen_mode=0
stubby_round_robin=0
stubby_mode=0'
if accepts 'four resolvers with IPv6' "$FOUR"; then
    count 'four resolvers with IPv6' 'address_data:' 4
    has 'four resolvers with IPv6' '  - address_data: "2001:4860:4860::8888"'
    has 'four resolvers with IPv6' 'round_robin_upstreams: 0'
fi

GAP='stubby_server0=
stubby_server_ip0=
stubby_server2=dns.google
stubby_server_ip2=8.8.8.8
stubby_listen_port=5453
stubby_listen_mode=0
stubby_round_robin=1
stubby_mode=1'
accepts 'resolver after an empty slot' "$GAP" && count 'resolver after an empty slot' 'address_data:' 1

OPPORTUNISTIC=$(printf '%s\n' "$DEFAULTS" | sed 's/^stubby_mode=.*/stubby_mode=3/')
if accepts 'opportunistic mode' "$OPPORTUNISTIC"; then
    has 'opportunistic mode' 'tls_authentication: GETDNS_AUTHENTICATION_NONE'
    has 'opportunistic mode' '  - GETDNS_TRANSPORT_UDP'
    has 'opportunistic mode' '  - GETDNS_TRANSPORT_TCP'
fi

LAN=$(printf '%s\n' "$DEFAULTS" | sed 's/^stubby_listen_mode=.*/stubby_listen_mode=1/')
accepts 'LAN listener' "$LAN" && has 'LAN listener' '  - "192.168.1.1@5453"'
ALL=$(printf '%s\n' "$DEFAULTS" | sed 's/^stubby_listen_mode=.*/stubby_listen_mode=2/')
accepts 'all-address listener' "$ALL" && has 'all-address listener' '  - "0.0.0.0@5453"'

with() { printf '%s\n' "$DEFAULTS" | sed "$1"; }
rejects 'no resolvers' 'No Stubby resolvers configured' "$(with '/^stubby_server/d')"
rejects 'name without address' 'Incomplete Stubby resolver 1' "$(with '$a\
stubby_server1=dns.quad9.net')"
rejects 'address without name' 'Incomplete Stubby resolver 0' "$(with '/^stubby_server0=/d')"
rejects 'short IPv4 address' 'Invalid address for resolver 0' "$(with 's/^stubby_server_ip0=.*/stubby_server_ip0=8.8.8/')"
rejects 'IPv4 octet over 255' 'Invalid address for resolver 0' "$(with 's/^stubby_server_ip0=.*/stubby_server_ip0=8.8.8.256/')"
rejects 'address with port' 'Invalid address for resolver 0' "$(with 's/^stubby_server_ip0=.*/stubby_server_ip0=8.8.8.8@853/')"
rejects 'name with port' 'Invalid TLS authentication name for resolver 0' "$(with 's/^stubby_server0=.*/stubby_server0=dns.google:853/')"
rejects 'name starting with dot' 'Invalid TLS authentication name for resolver 0' "$(with 's/^stubby_server0=.*/stubby_server0=.dns.google/')"
rejects 'missing port' 'Invalid Stubby listen port' "$(with '/^stubby_listen_port=/d')"
rejects 'port over 65535' 'between 1 and 65535' "$(with 's/^stubby_listen_port=.*/stubby_listen_port=70000/')"
rejects 'missing round-robin' 'Invalid Stubby round-robin setting' "$(with '/^stubby_round_robin=/d')"
rejects 'unknown listen mode' 'Invalid Stubby listen mode' "$(with 's/^stubby_listen_mode=.*/stubby_listen_mode=3/')"
rejects 'LAN listener without LAN address' 'Invalid LAN listen address' "$(with 's/^stubby_listen_mode=.*/stubby_listen_mode=1/;/^lan_ipaddr_t=/d')"
rejects 'unknown privacy mode' 'Invalid Stubby privacy mode' "$(with 's/^stubby_mode=.*/stubby_mode=4/')"
rejects 'missing CA bundle' 'Stubby CA bundle is missing' "$DEFAULTS" 0 "$work/share/missing.crt"
rejects 'stubby rejects generated file' 'Stubby rejected the generated configuration' "$DEFAULTS" 1

if [ "$failures" -ne 0 ]; then
    echo "FAIL $failures Stubby configuration case(s)"
    exit 1
fi
echo 'PASS stubby.sh configuration: accepted layouts, all rejection paths and retained previous configuration'
