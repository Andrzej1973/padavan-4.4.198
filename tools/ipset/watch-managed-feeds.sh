#!/bin/sh
# Single supervisor for the Classic IPSet refresh service.
set -eu
umask 077

refresh=${WR_CLASSIC_IPSET_REFRESH:-/usr/sbin/wr-classic-ipset-refresh}
config=${WR_CLASSIC_IPSET_CONFIG:-/etc/storage/wr-classic-ipset.feeds}
lock=${WR_CLASSIC_IPSET_LOCK:-/var/run/wr-classic-ipset.worker}
mkdir "$lock" || exit 1
cleanup() {
    rm -f "$lock/pid"
    rmdir "$lock"
}
trap cleanup EXIT
trap 'exit 0' HUP INT TERM
printf '%s\n' "$$" >"$lock/pid"

last_attempt=0
last_settings=
while :; do
    enabled=$(nvram get wr_classic_ipset_enable)
    hours=$(nvram get wr_classic_ipset_period)
    case "$hours" in
        0|6|12|24|48|72|168|336) ;;
        *) hours=0 ;;
    esac
    checksum=
    if [ "$enabled" = 1 ] && [ -f "$config" ] && [ "$(wc -c <"$config")" -le 8192 ]; then
        checksum=$(cksum <"$config")
    fi
    settings="$enabled:$hours:$checksum"
    if [ "$enabled" = 1 ]; then
        read -r uptime rest </proc/uptime
        now=${uptime%%.*}
        if [ "$settings" != "$last_settings" ] ||
            { [ "$hours" -gt 0 ] && [ "$((now - last_attempt))" -ge "$((hours * 3600))" ]; }; then
            last_attempt=$now
            "$refresh" "$config" || :
        fi
    fi
    last_settings=$settings
    sleep 30
done
