#!/bin/sh
# Read-only post-flash checks. Run on the router: sh check-device-readonly.sh
set -u
fail=0
say() { echo "$1"; }
ok() { say "PASS $1"; }
bad() { say "FAIL $1"; fail=1; }

# Require a unique retained cursor. Counting the whole rotating log can report
# zero growth while new noise replaces older lines, or when the log is missing.
check_log_window() {
    logfile=$1
    if [ ! -r "$logfile" ] || [ ! -s "$logfile" ]; then
        say "UNKNOWN log window: journal unavailable"; return 2
    fi
    anchor=$(tail -n 1 "$logfile" 2>/dev/null) || {
        say "UNKNOWN log window: cannot read cursor"; return 2;
    }
    if [ -z "$anchor" ]; then say "UNKNOWN log window: empty cursor"; return 2; fi
    sleep 30 || { say "UNKNOWN log window: wait failed"; return 2; }
    window=$(WR_LOG_ANCHOR="$anchor" awk '
        $0 == ENVIRON["WR_LOG_ANCHOR"] { found++; next }
        found { if (index($0,"BndStrg_InfStatusRsp")) status++;
                if (index($0,"Reaped")) reaped++ }
        END { if (found != 1) print "unknown";
              else if (status || reaped) printf "noise status=%d reaper=%d\n",status,reaped;
              else print "clean" }
    ' "$logfile" 2>/dev/null) || {
        say "UNKNOWN log window: read failed"; return 2;
    }
    case "$window" in
        clean) ok "no new status-query/reaper log noise in 30 s"; return 0 ;;
        noise\ *) say "FAIL new log $window in 30 s"; return 1 ;;
        *) say "UNKNOWN log window: cursor lost or ambiguous (rotation/truncation)"; return 2 ;;
    esac
}

# Isolated read-only journal check, also used by host fixtures.
if [ "${1:-}" = "--log-window" ]; then
    [ "$#" -eq 2 ] || exit 2
    check_log_window "$2"
    exit $?
fi

say "firmware=$(nvram get firmver 2>/dev/null) build=$(nvram get buildno 2>/dev/null)"
[ -x /usr/sbin/wr-vpn-profile ] && ok "manager binary" || bad "manager binary"
[ -x /usr/sbin/wr-vpn-profiles-service ] && ok "service script" || bad "service script"
[ -x /usr/libexec/wrvpn/action-worker ] && ok "action worker" || bad "action worker"
/usr/sbin/wr-vpn-profile list >/dev/null 2>&1 && ok "profile list" || bad "profile list"

check_log_window /tmp/syslog.log || fail=1

ip -4 addr show br0 2>/dev/null | grep -q '192\.168\.20\.1/' && ok "LAN address" || bad "LAN address"
ip route 2>/dev/null | grep -q '^default ' && ok "default route" || bad "default route"
wg_bin=$(command -v wg 2>/dev/null)
if [ -z "${wg_bin:-}" ] && [ -x /usr/sbin/wg ]; then wg_bin=/usr/sbin/wg; fi
if [ -z "${wg_bin:-}" ] && [ -x /usr/bin/wg ]; then wg_bin=/usr/bin/wg; fi
if [ -n "${wg_bin:-}" ] && [ -x "$wg_bin" ]; then
    if "$wg_bin" show interfaces 2>/dev/null | grep -q .; then
        ok "tunnel interface present"
    else
        say "NOTE no WireGuard interface"
    fi
fi

[ "$fail" = "0" ] && say "RESULT OK" || say "RESULT FAILED"
exit "$fail"
