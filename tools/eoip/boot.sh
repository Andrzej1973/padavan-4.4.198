#!/bin/sh
# Candidate boot policy. Not installed until RC integration is complete.
# NVRAM is read only: persistence remains the firmware's explicit save operation.
# Never evaluate configuration as shell code; pass each field as one argument.

case "${1-}" in
    boot|stop) action=$1 ;;
    *) echo 'usage: wr-eoip-boot boot|stop' >&2; exit 64 ;;
esac

result=0
master=0
if [ "$action" = boot ]; then
    master=$(nvram get eoip_enable) || exit 67
fi
slot=0
while [ "$slot" -lt 8 ]; do
    if [ "$action" = stop ] || [ "$master" != 1 ]; then
        # Cleanup must not depend on a valid endpoint or profile.
        /usr/bin/eoip-service stop "$slot" || result=67
    else
        prefix="eoip_slot${slot}"
        enabled=$(nvram get "${prefix}_enable") || exit 67
        autostart=$(nvram get "${prefix}_autostart") || exit 67
        if [ "$enabled" = 1 ] && [ "$autostart" = 1 ]; then
            local_address=$(nvram get "${prefix}_local") || exit 67
            remote_address=$(nvram get "${prefix}_remote") || exit 67
            tunnel_id=$(nvram get "${prefix}_id") || exit 67
            mtu=$(nvram get "${prefix}_mtu") || exit 67
            keepalive=$(nvram get "${prefix}_keepalive") || exit 67
            retries=$(nvram get "${prefix}_retries") || exit 67
            bridge=$(nvram get "${prefix}_bridge") || exit 67
            /usr/bin/eoip-service start "$slot" 1 1 "$local_address" \
                "$remote_address" "$tunnel_id" "$mtu" "$keepalive" \
                "$retries" "$bridge" || result=67
        fi
    fi
    slot=$((slot + 1))
done
exit "$result"
