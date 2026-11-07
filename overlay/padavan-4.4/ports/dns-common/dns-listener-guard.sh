#!/bin/sh
# Shared bind-address/port collision check for the Stubby and DoH listeners.
# A wildcard IPv4 bind overlaps every other IPv4 listener address.
WR_DOH_BINARY=${WR_DOH_BINARY:-/usr/sbin/https_dns_proxy}
WR_STUBBY_BINARY=${WR_STUBBY_BINARY:-/usr/sbin/stubby}

wr_dns_listener_decimal()
{
    case "$1" in ''|*[!0-9]*) return 1;; esac
    [ "${#1}" -le 5 ] || return 1
    printf '%s\n' "$1" | awk '{printf "%.0f", $0 + 0}'
}

wr_dns_listener_address_for_mode()
{
    case "$1" in
        0) printf '%s\n' 127.0.0.1;;
        1) nvram get lan_ipaddr_t;;
        2) printf '%s\n' 0.0.0.0;;
        *) return 1;;
    esac
}

wr_dns_listener_addresses_overlap()
{
    [ "$1" = "$2" ] || [ "$1" = 0.0.0.0 ] || [ "$2" = 0.0.0.0 ]
}

wr_dns_listener_conflict()
{
    local service own_address own_port other other_port other_mode other_address
    local index url candidate_port
    service=$1
    own_address=$2
    own_port=$(wr_dns_listener_decimal "$3") || return 0
    case "$service" in
        stubby)
            [ "$(nvram get doh_enable)" = 1 ] || return 0
            [ -x "$WR_DOH_BINARY" ] || return 0
            other=doh
            other_port=$(nvram get doh_listen_port)
            other_mode=$(nvram get doh_listen_mode)
            other_address=$(wr_dns_listener_address_for_mode "$other_mode") || {
                echo 'Cannot verify enabled DoH listener: invalid bind mode' >&2
                return 1
            }
            other_port=$(wr_dns_listener_decimal "$other_port") || {
                echo 'Cannot verify enabled DoH listener: invalid port' >&2
                return 1
            }
            [ "$other_port" -ge 1 ] && [ "$other_port" -le 65532 ] || {
                echo 'Cannot verify enabled DoH listener: port outside 1..65532' >&2
                return 1
            }
            wr_dns_listener_addresses_overlap "$own_address" "$other_address" || return 0
            for index in 0 1 2 3; do
                url=$(nvram get "doh_server$index")
                case "$url" in https://?*) ;; *) continue;; esac
                candidate_port=$((other_port + index))
                if [ "$own_port" -eq "$candidate_port" ]; then
                    echo "DNS listener conflict: Stubby and DoH both bind $own_address:$own_port" >&2
                    return 1
                fi
            done
            ;;
        doh)
            [ "$(nvram get stubby_enable)" = 1 ] || return 0
            [ -x "$WR_STUBBY_BINARY" ] || return 0
            other=stubby
            other_port=$(nvram get stubby_listen_port)
            other_mode=$(nvram get stubby_listen_mode)
            other_address=$(wr_dns_listener_address_for_mode "$other_mode") || {
                echo 'Cannot verify enabled Stubby listener: invalid bind mode' >&2
                return 1
            }
            other_port=$(wr_dns_listener_decimal "$other_port") || {
                echo 'Cannot verify enabled Stubby listener: invalid port' >&2
                return 1
            }
            [ "$other_port" -ge 1024 ] && [ "$other_port" -le 65535 ] || {
                echo 'Cannot verify enabled Stubby listener: port outside 1024..65535' >&2
                return 1
            }
            wr_dns_listener_addresses_overlap "$own_address" "$other_address" || return 0
            for index in 0 1 2 3; do
                url=$(nvram get "doh_server$index")
                case "$url" in https://?*) ;; *) continue;; esac
                candidate_port=$((own_port + index))
                if [ "$other_port" -eq "$candidate_port" ]; then
                    echo "DNS listener conflict: DoH and Stubby both bind $other_address:$other_port" >&2
                    return 1
                fi
            done
            ;;
        *) return 2;;
    esac
    return 0
}
