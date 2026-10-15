#!/bin/sh
# The target worker reads NVRAM and applies it under one operation lock.
# No shell interpolation of profile values; no NVRAM writes or flash commit.
case "${1-}" in
    boot) exec /usr/bin/eoip-service boot-stored ;;
    apply) exec /usr/bin/eoip-service apply-stored ;;
    stop) exec /usr/bin/eoip-service stop-table ;;
    *) echo 'usage: wr-eoip-boot boot|apply|stop' >&2; exit 64 ;;
esac
