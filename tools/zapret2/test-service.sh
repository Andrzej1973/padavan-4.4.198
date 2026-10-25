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
    wan_ifname|wan0_ifname) printf '%s\n' "${MOCK_WAN-eth3}" ;;
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
        : >"$jump"
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
    MOCK_WAN=${MOCK_WAN-eth3} \
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

grep -q -- '--queue-bypass' "$SERVICE" || fail "NFQUEUE fail-open flag is absent"
if grep -q -- '-j LOG' "$SERVICE"; then
    fail "service installs a LOG rule"
fi

printf 'PASS Zapret2 host lifecycle checks\n'
