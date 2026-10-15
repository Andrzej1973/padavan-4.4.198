#!/bin/sh
# NVRAM boot/apply/shutdown policy. HTTP authentication is a separate caller.
# NVRAM is read only: persistence remains the firmware's explicit save operation.
# Never evaluate configuration as shell code; pass each field as one argument.

case "${1-}" in
    boot|apply|stop) action=$1 ;;
    *) echo 'usage: wr-eoip-boot boot|apply|stop' >&2; exit 64 ;;
esac

if [ "$action" = stop ]; then
    # Cleanup never depends on NVRAM or validity of stored profiles.
    exec /usr/bin/eoip-service stop-table
fi
master=$(nvram get eoip_enable) || exit 67
case "$master" in
    1) ;;
    0|'')
        [ "$action" = boot ] && exit 0
        exec /usr/bin/eoip-service stop-table ;;
    *) echo 'invalid EoIP master flag' >&2; exit 65 ;;
esac
slot=0
if [ "$action" = apply ]; then set -- apply-table; else set -- boot-table; fi
while [ "$slot" -lt 8 ]; do
    prefix="eoip_slot${slot}"
    enabled=$(nvram get "${prefix}_enable") || exit 67
    autostart=$(nvram get "${prefix}_autostart") || exit 67
    # Snapshot every profile before the worker performs any mutation.
    local_address=$(nvram get "${prefix}_local") || exit 67
    remote_address=$(nvram get "${prefix}_remote") || exit 67
    tunnel_id=$(nvram get "${prefix}_id") || exit 67
    mtu=$(nvram get "${prefix}_mtu") || exit 67
    keepalive=$(nvram get "${prefix}_keepalive") || exit 67
    retries=$(nvram get "${prefix}_retries") || exit 67
    bridge=$(nvram get "${prefix}_bridge") || exit 67
    set -- "$@" "$slot" "$enabled" "$autostart" "$local_address" \
        "$remote_address" "$tunnel_id" "$mtu" "$keepalive" "$retries" "$bridge"
    slot=$((slot + 1))
done
modprobe eoip || exit 67
exec /usr/bin/eoip-service "$@"
