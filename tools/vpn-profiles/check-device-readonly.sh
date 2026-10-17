#!/bin/sh
# Read-only post-flash checks. Run on the router: sh check-device-readonly.sh
set -u
fail=0
say() { echo "$1"; }
ok() { say "PASS $1"; }
bad() { say "FAIL $1"; fail=1; }

say "firmware=$(nvram get firmver 2>/dev/null) build=$(nvram get buildno 2>/dev/null)"
[ -x /usr/sbin/wr-vpn-profile ] && ok "manager binary" || bad "manager binary"
[ -x /usr/sbin/wr-vpn-profiles-service ] && ok "service script" || bad "service script"
[ -x /usr/libexec/wrvpn/action-worker ] && ok "action worker" || bad "action worker"
/usr/sbin/wr-vpn-profile list >/dev/null 2>&1 && ok "profile list" || bad "profile list"

sample_noise() { n=$(grep -c 'BndStrg_InfStatusRsp' /tmp/syslog.log 2>/dev/null); echo "${n:-0}"; }
before=$(sample_noise)
sleep 30
after=$(sample_noise)
delta=$((after - before))
[ "$delta" -le 0 ] && ok "no status-query log noise in 30 s" || bad "status-query log noise (${delta} in 30 s)"
reaped=$(grep -c 'Reaped' /tmp/syslog.log 2>/dev/null)
reaped=${reaped:-0}
[ "$reaped" = "0" ] && ok "no reaper log noise" || bad "reaper log noise ($reaped)"

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
