#!/bin/sh
# Candidate lifecycle helper; rc applies enable/AP-mode policy.
set -eu
storage=/etc/storage/privoxy
defaults=/usr/share/privoxy/privoxy
binary=/usr/sbin/privoxy
pidfile=/var/run/privoxy.pid

prepare_config()
{
    test -x "$binary"
    test -d "$defaults"
    mkdir -p "$storage"
    created=0
    # Only seed missing files; keep every existing user file byte-for-byte.
    for name in config default.filter user.filter default.action match-all.action user.action user.trust; do
        if [ ! -e "$storage/$name" ] && [ ! -L "$storage/$name" ]; then
            test -f "$defaults/$name"
            cp "$defaults/$name" "$storage/$name"
            chmod 644 "$storage/$name"
            if [ "$name" = config ]; then
                address="$(ip -4 address show dev br0 | awk '/inet / {split($2,a,"/"); print a[1]; exit}')"
                if [ -z "$address" ]; then
                    rm -f "$storage/config"
                    logger -t privoxy 'Cannot initialize configuration: br0 has no IPv4 address'
                    return 1
                fi
                sed -i "s/^listen-address.*/listen-address  $address:8118/" "$storage/config"
            fi
            created=1
        fi
    done
    if [ ! -e "$storage/templates" ] && [ ! -L "$storage/templates" ]; then
        ln -s /usr/share/privoxy/templates "$storage/templates"
        created=1
    fi
    if [ "$created" = 1 ]; then
        /sbin/mtd_storage.sh save
    fi
}

running()
{
    test -f "$pidfile" || return 1
    pid="$(cat "$pidfile")"
    case "$pid" in ''|*[!0-9]*|0|1) return 1;; esac
    test "$(cat "/proc/$pid/comm" 2>/dev/null || :)" = privoxy || return 1
    kill -0 "$pid" 2>/dev/null
}

start_service()
{
    if running; then return 0; fi
    if pidof privoxy >/dev/null 2>&1; then
        logger -t privoxy 'Existing process has no verified PID file; refusing duplicate start'
        return 1
    fi
    rm -f "$pidfile"
    prepare_config
    if ! "$binary" --no-daemon --config-test "$storage/config"; then
        logger -t privoxy 'Configuration rejected; service was not started'
        return 1
    fi
    # The daemon must not keep the lifecycle lock open after fork.
    "$binary" --pidfile "$pidfile" "$storage/config" 9>&-
    sleep 1
    if ! running; then
        logger -t privoxy 'Process did not remain running after startup'
        return 1
    fi
    logger -t privoxy 'Started' 
}

stop_service()
{
    # Matches the original service stop policy, including manual starts.
    if pidof privoxy >/dev/null 2>&1; then
        killall -q privoxy
        attempts=0
        while pidof privoxy >/dev/null 2>&1; do
            attempts=$((attempts + 1))
            if [ "$attempts" -ge 10 ]; then
                logger -t privoxy 'Stop timed out; restart aborted'
                return 1
            fi
            sleep 1
        done
    fi
}

# One lock covers stop, configuration preparation and start during restart.
case "${1:-}" in
    start|stop|restart|check) ;;
    *) echo "Usage: $0 {start|stop|restart|check}" >&2; exit 1;;
esac
command -v flock >/dev/null || { echo 'Privoxy requires flock' >&2; exit 1; }
exec 9>/var/run/privoxy-service.lock
flock -x -n 9 || { echo 'Another Privoxy operation is in progress' >&2; exit 1; }

case "${1:-}" in
    start) start_service;;
    stop) stop_service;;
    restart) stop_service; start_service;;
    check) "$binary" --no-daemon --config-test "$storage/config";;
    *) echo "Usage: $0 {start|stop|restart|check}" >&2; exit 1;;
esac
