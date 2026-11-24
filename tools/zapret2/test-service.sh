#!/bin/sh
# Host-side lifecycle checks for tools/zapret2/service.sh.
# Uses command mocks; it does not load kernel modules or change firewall state.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SERVICE="$HERE/service.sh"
TMP=$(mktemp -d)
MOCK="$TMP/bin"
STATE="$TMP/state"
LUA="$TMP/lua"
REAL_PATH=$PATH
REAL_SLEEP=$(command -v sleep)

cleanup() {
    if [ -f "$TMP/pid" ]; then
        ZAPRET2_PATH="$MOCK:$REAL_PATH" \
        ZAPRET2_NFQWS2="$MOCK/nfqws2" \
        ZAPRET2_ARGS="$TMP/args" \
        ZAPRET2_PIDFILE="$TMP/pid" \
        ZAPRET2_LUA_DIR="$LUA" \
            sh "$SERVICE" stop >/dev/null 2>&1 || true
    fi
    rm -rf "$TMP"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$MOCK" "$STATE" "$LUA"
printf '%s\n' '--filter-tcp=443' >"$TMP/args"
: >"$LUA/zapret-lib.lua"
: >"$LUA/zapret-antidpi.lua"
: >"$LUA/zapret-auto.lua"

cat >"$MOCK/nvram" <<'EOF'
#!/bin/sh
[ "$1" = get ] || exit 2
case "$2" in
    zapret2_iface) printf '%s\n' "${MOCK_IFACE-}" ;;
    zapret2_clients_mode) printf '%s\n' "${MOCK_CLIENT_MODE-exclude}" ;;
    zapret2_profile) printf '%s\n' "${MOCK_PROFILE-0}" ;;
    zapret2_host_auto) printf '%s\n' "${MOCK_HOST_AUTO-0}" ;;
    zapret2_post_enable) printf '%s\n' "${MOCK_POST_ENABLE-0}" ;;
    zapret2_log) printf '%s\n' "${MOCK_LOG-0}" ;;
    wan_ifname|wan0_ifname) printf '%s\n' "${MOCK_WAN-lo}" ;;
    *) exit 1 ;;
esac
EOF

cat >"$MOCK/sleep" <<'EOF'
#!/bin/sh
exit 0
EOF

cat >"$MOCK/nfqws2" <<EOF
#!/bin/sh
printf '%s\n' "\$@" >"\${MOCK_STATE:?}/nfqws-args"
trap 'exit 0' TERM INT
while :; do
    "$REAL_SLEEP" 5
done
EOF

cat >"$MOCK/iptables" <<'EOF'
#!/bin/sh
set -eu
state=${MOCK_STATE:?}
chain="$state/chain"
jump="$state/jump"
nfqueue="$state/nfqueue"
case "$*" in
    "-t mangle -S POSTROUTING")
        if [ -f "$jump" ]; then cat "$jump"; fi
        ;;
    "-t mangle -n -L ZAPRET2") test -f "$chain" ;;
    "-t mangle -N ZAPRET2")
        test ! -e "$chain"
        : >"$chain"
        ;;
    "-t mangle -F ZAPRET2")
        test -f "$chain"
        rm -f "$nfqueue"
        ;;
    "-t mangle -X ZAPRET2")
        test -f "$chain"
        rm -f "$chain" "$jump" "$nfqueue"
        ;;
    "-t mangle -I POSTROUTING 1 -o "*" -j ZAPRET2")
        printf "%s\n" "-A POSTROUTING -o $7 -j ZAPRET2" >"$jump"
        ;;
    "-t mangle -C POSTROUTING -o "*" -j ZAPRET2")
        test -f "$jump"
        ;;
    "-t mangle -C ZAPRET2 -p tcp -j NFQUEUE --queue-num 200 --queue-bypass"|\
    "-t mangle -C ZAPRET2 -p udp -j NFQUEUE --queue-num 200 --queue-bypass")
        test -f "$nfqueue"
        ;;
    "-t mangle -D POSTROUTING -o "*" -j ZAPRET2"|\
    "-t mangle -D POSTROUTING -j ZAPRET2")
        test -f "$jump" || exit 1
        rm -f "$jump"
        ;;
    "-t mangle -A ZAPRET2 -p tcp -j NFQUEUE --queue-num 200 --queue-bypass"|\
    "-t mangle -A ZAPRET2 -p udp -j NFQUEUE --queue-num 200 --queue-bypass")
        : >"$nfqueue"
        ;;
    "-t mangle -A ZAPRET2 "*) : ;;
    *) printf 'unexpected iptables call: %s\n' "$*" >&2; exit 2 ;;
esac
EOF

chmod +x "$MOCK/nvram" "$MOCK/sleep" "$MOCK/nfqws2" "$MOCK/iptables"

run_service() {
    MOCK_STATE="$STATE" \
    MOCK_WAN=${MOCK_WAN-lo} \
    ZAPRET2_PATH="$MOCK:$REAL_PATH" \
    ZAPRET2_NFQWS2="$MOCK/nfqws2" \
    ZAPRET2_ARGS="$TMP/args" \
    ZAPRET2_PIDFILE="$TMP/pid" \
    ZAPRET2_LUA_DIR="$LUA" \
        sh "$SERVICE" "$@"
}

fail() {
    printf 'FAIL Zapret2 service test: %s\n' "$*" >&2
    exit 1
}

sh -n "$SERVICE" || fail "shell syntax"
mv "$LUA/zapret-auto.lua" "$TMP/zapret-auto.lua"
if run_service start >/dev/null 2>&1; then
    fail "missing Lua support was accepted"
fi
mv "$TMP/zapret-auto.lua" "$LUA/zapret-auto.lua"
dd if=/dev/zero bs=8193 count=1 2>/dev/null | tr '\000' x >"$TMP/args"
if run_service start >/dev/null 2>&1; then
    fail "oversized strategy was accepted"
fi
printf '%s\n' '--filter-tcp=443' >"$TMP/args"
run_service start >"$TMP/start.out" || fail "start returned an error"
grep -qx 'started' "$TMP/start.out" || fail "start did not report success"
test -f "$STATE/chain" || fail "mangle chain was not created"
test -f "$STATE/jump" || fail "POSTROUTING hook was not installed"
test -f "$STATE/nfqueue" || fail "NFQUEUE rules were not installed"
test -s "$TMP/pid" || fail "PID file was not written"
grep -q -- "--lua-init=@$LUA/zapret-lib.lua" "$STATE/nfqws-args" ||
    fail "Lua library was not passed to nfqws2"
grep -q -- "--lua-init=@$LUA/zapret-antidpi.lua" "$STATE/nfqws-args" ||
    fail "antidpi library was not passed to nfqws2"
grep -q -- "--lua-init=@$LUA/zapret-auto.lua" "$STATE/nfqws-args" ||
    fail "autohostlist library was not passed to nfqws2"
run_service status >"$TMP/status.out" || fail "status returned an error"
grep -qx 'process=running' "$TMP/status.out" || fail "running process was not observed"
grep -qx 'rules=installed' "$TMP/status.out" || fail "installed rules were not observed"
run_service start >"$TMP/second.out" || fail "idempotent start failed"
grep -qx 'already running' "$TMP/second.out" || fail "idempotent start was not reported"

rm -f "$STATE/nfqueue"
run_service status >"$TMP/lost.out"
grep -qx 'rules=absent' "$TMP/lost.out" || fail "missing hook was not observed"
run_service restart >/dev/null || fail "restart did not reconcile the hook"
test -f "$STATE/jump" || fail "restart did not restore the hook"
test -f "$STATE/nfqueue" || fail "restart did not restore NFQUEUE rules"

run_service stop >"$TMP/stop.out" || fail "stop returned an error"
grep -qx 'stopped' "$TMP/stop.out" || fail "stop did not report success"
test ! -e "$STATE/chain" || fail "mangle chain remains after stop"
test ! -e "$STATE/jump" || fail "POSTROUTING hook remains after stop"
test ! -e "$STATE/nfqueue" || fail "NFQUEUE rules remain after stop"
test ! -e "$TMP/pid" || fail "PID file remains after stop"

printf '%s\n' "$$" >"$TMP/pid"
run_service stop >/dev/null || fail "stale PID cleanup failed"
test ! -e "$TMP/pid" || fail "stale PID file remains"

: >"$TMP/args"
if run_service start >/dev/null 2>&1; then
    fail "empty strategy was accepted"
fi
printf '%s\n' '--filter-tcp=443' >"$TMP/args"
MOCK_WAN='' run_service start >/dev/null 2>&1 && fail "missing WAN was accepted"

MOCK_WAN=missing0 MOCK_IFACE=lo MOCK_LOG=1 run_service start >/dev/null ||
    fail "explicit interface and logging were not accepted"
grep -qx -- '--debug=syslog' "$STATE/nfqws-args" ||
    fail "syslog option was not passed to nfqws2"
MOCK_IFACE=missing0 run_service stop >/dev/null ||
    fail "stop did not remove the prior interface hook"

printf '%s\n' '--filter-tcp=8443' >"$TMP/args.10"
MOCK_PROFILE=10 run_service start >/dev/null || fail "profile 10 did not start"
grep -qx -- '--filter-tcp=8443' "$STATE/nfqws-args" || fail "wrong profile arguments"
run_service stop >/dev/null || fail "profile 10 did not stop"
if MOCK_PROFILE=11 run_service start >/dev/null 2>&1; then
    fail "invalid profile was accepted"
fi
if MOCK_PROFILE=1 run_service start >/dev/null 2>&1; then
    fail "missing profile was accepted"
fi

printf '%s\n' '192.168.20.0/24 # clients' >"$TMP/zapret2.clients-exclude"
run_service rules >"$TMP/rules.out" || fail "valid client exclusion was rejected"
grep -qx -- 'iptables -t mangle -A ZAPRET2 -s 192.168.20.0/24 -j RETURN' "$TMP/rules.out" ||
    fail "missing source exclusion rule"
printf '%s\n' '198.51.100.0/24' >"$TMP/zapret2.destinations-exclude"
run_service rules >"$TMP/rules.out" || fail "valid destination exclusion was rejected"
grep -qx -- 'iptables -t mangle -A ZAPRET2 -d 198.51.100.0/24 -j RETURN' "$TMP/rules.out" ||
    fail "missing destination exclusion rule"
run_service start >/dev/null || fail "start with client exclusion failed"
run_service stop >/dev/null || fail "stop after client exclusion failed"
printf '%s\n' '192.168.20.1/33' >"$TMP/zapret2.clients-exclude"
if run_service start >/dev/null 2>&1; then
    fail "invalid client exclusion was accepted"
fi
test ! -e "$STATE/jump" || fail "invalid exclusion installed a firewall hook"
rm -f "$TMP/zapret2.clients-exclude"
printf '%s\n' '198.51.100.256' >"$TMP/zapret2.destinations-exclude"
if run_service start >/dev/null 2>&1; then
    fail "invalid destination exclusion was accepted"
fi
test ! -e "$STATE/jump" || fail "invalid destination exclusion installed a firewall hook"


rm -f "$TMP/zapret2.destinations-exclude"
printf '%s\n' '192.0.2.4' >"$TMP/zapret2.clients-exclude"
MOCK_CLIENT_MODE=include run_service rules >"$TMP/rules.out" ||
    fail "could not describe selected-client rules"
grep -qx -- 'iptables -t mangle -A ZAPRET2 -m set ! --match-set wr_classic_zapret2_clients src -j RETURN' "$TMP/rules.out" ||
    fail "missing selected-client filter"
if MOCK_CLIENT_MODE=include ZAPRET2_IPSET_APPLY="$TMP/missing" run_service start >/dev/null 2>&1; then
    fail "selected-client mode accepted a missing IPSet helper"
fi
test ! -e "$STATE/jump" || fail "missing IPSet helper installed a firewall hook"

printf '%s\n' 'example.test' >"$TMP/zapret2.hosts"
printf '%s\n' 'excluded.example.test' >"$TMP/zapret2.hosts-exclude"
printf '%s\n' '--filter-tcp=443' '--new=udp --filter-udp=443' >"$TMP/args"
run_service start >/dev/null || fail "strategy with domain lists did not start"
grep -E -- '^(--hostlist|--new|--filter)' "$STATE/nfqws-args" >"$TMP/domain-args"
printf '%s\n' "--hostlist=$TMP/zapret2.hosts" "--hostlist-exclude=$TMP/zapret2.hosts-exclude" \
    '--filter-tcp=443' '--new=udp' "--hostlist=$TMP/zapret2.hosts" \
    "--hostlist-exclude=$TMP/zapret2.hosts-exclude" '--filter-udp=443' >"$TMP/domain-expected"
cmp -s "$TMP/domain-expected" "$TMP/domain-args" || fail "domain lists did not bind to both profiles"
run_service stop >/dev/null || fail "stop after domain strategy failed"

printf '%s\n' '203.0.113.0/24#comment' '192.0.2.1' >"$TMP/zapret2.destinations"
run_service start >/dev/null || fail "strategy with destination list did not start"
count=$(grep -Fxc -- "--ipset-ip=203.0.113.0/24,192.0.2.1" "$STATE/nfqws-args")
test "$count" -eq 2 || fail "destination list did not bind to both profiles"
run_service stop >/dev/null || fail "stop after destination strategy failed"
printf '%s\n' '203.0.113.256' >"$TMP/zapret2.destinations"
if run_service start >/dev/null 2>&1; then
    fail "invalid destination list accepted"
fi
test ! -e "$STATE/jump" || fail "invalid destination list installed a firewall hook"
rm -f "$TMP/zapret2.destinations"

MOCK_HOST_AUTO=1 run_service start >/dev/null || fail "automatic domain strategy did not start"
test -f "$TMP/zapret2.hosts-auto" || fail "automatic list was not created"
count=$(grep -Fxc -- "--hostlist-auto=$TMP/zapret2.hosts-auto" "$STATE/nfqws-args")
test "$count" -eq 2 || fail "automatic list did not bind to both profiles"
run_service stop >/dev/null || fail "stop after automatic domain strategy failed"

printf 'touch "%s"\n' "$TMP/post-ran" >"$TMP/zapret2.post-start.sh"
run_service start >/dev/null || fail "disabled hook test did not start"
test ! -e "$TMP/post-ran" || fail "post-start hook ran without opt-in"
run_service stop >/dev/null || fail "disabled hook test did not stop"
MOCK_POST_ENABLE=1 run_service start >/dev/null || fail "enabled hook test did not start"
test -f "$TMP/post-ran" || fail "enabled post-start hook did not run"
run_service stop >/dev/null || fail "enabled hook test did not stop"



mkdir "$TMP/presets"
printf '%s\n' '--filter-tcp=9443' >"$TMP/presets/strategy5"
MOCK_PROFILE=preset5 ZAPRET2_PRESETS="$TMP/presets" run_service start >/dev/null ||
    fail "built-in profile 5 did not start"
grep -qx -- '--filter-tcp=9443' "$STATE/nfqws-args" || fail "wrong built-in strategy arguments"
grep -qx -- "--hostlist=$TMP/zapret2.hosts" "$STATE/nfqws-args" ||
    fail "built-in strategy did not use the storage-side domain list"
run_service stop >/dev/null || fail "built-in strategy did not stop"
rm -f "$TMP/zapret2.hosts"
if MOCK_PROFILE=preset5 ZAPRET2_PRESETS="$TMP/presets" run_service start >/dev/null 2>&1; then
    fail "built-in strategy accepted a missing domain list"
fi

grep -q -- '--queue-bypass' "$SERVICE" || fail "NFQUEUE fail-open flag is absent"
if grep -q -- '-j LOG' "$SERVICE"; then
    fail "service installs a LOG rule"
fi

printf 'PASS Zapret2 host lifecycle checks\n'
