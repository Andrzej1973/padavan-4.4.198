#!/bin/sh
# Exercises service.sh with fake nvram/controller binaries; nothing is started.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(mktemp -d)
bin=$root/bin
mkdir -p "$bin"
calls=$root/calls

cat > "$bin/nvram" <<'EOS'
#!/bin/sh
case "$2" in
    wrvpn_enabled) echo "3,5";;
    wrvpn_protect) echo "192.168.20.0/24";;
    *) exit 1;;
esac
EOS
cat > "$bin/wr-vpn-profile" <<EOS
#!/bin/sh
echo "ctl \$*" >> "$calls"
EOS
cat > "$bin/logger" <<'EOS'
#!/bin/sh
exit 0
EOS
chmod +x "$bin/nvram" "$bin/wr-vpn-profile" "$bin/logger"

run()
{
    PATH="$bin:$PATH" WRVPN_CTL="$bin/wr-vpn-profile" WRVPN_LOCK="$root/lock" \
        sh "$here/service.sh" "$1"
}

: > "$calls"
run start
test "$(cat "$calls")" = "ctl up 3 192.168.20.0/24
ctl up 5 192.168.20.0/24"

: > "$calls"
run stop
test "$(cat "$calls")" = "ctl down 3
ctl down 5"

: > "$calls"
run status
test "$(cat "$calls")" = "ctl plan 3
ctl plan 5"

cat > "$bin/nvram" <<'EOS'
#!/bin/sh
case "$2" in
    wrvpn_enabled) echo "3,abc";;
    wrvpn_protect) echo "192.168.20.0/24";;
    *) exit 1;;
esac
EOS
chmod +x "$bin/nvram"
: > "$calls"
if run start 2>/dev/null; then
    echo 'invalid id was accepted' >&2
    exit 1
fi
test "$(cat "$calls")" = "ctl up 3 192.168.20.0/24"

: > "$calls"
if run frobnicate 2>/dev/null; then
    echo 'unknown action was accepted' >&2
    exit 1
fi
test ! -s "$calls"

rm -rf "$root"
echo 'PASS VPN profile service: up/down/status argument passing, protected prefixes, invalid id refusal, no unstarted work'
