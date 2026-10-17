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
        WRVPN_DNS_DIR="$root/dns" WRVPN_RUN_DIR="$root/run" \
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

mkdir -p "$root/dns" "$root/run/3"
printf '1.1.1.1\n8.8.8.8\nbad entry\n' > "$root/run/3/wrv3.dns"
cat > "$bin/nvram" <<'EOS'
#!/bin/sh
case "$2" in
    wrvpn_enabled) echo "3";;
    wrvpn_protect) echo "192.168.20.0/24";;
    wrvpn_use_dns) echo "1";;
    *) exit 1;;
esac
EOS
chmod +x "$bin/nvram"
: > "$calls"
run start
test "$(cat "$root/dns/wrvpn.servers")" = "server=1.1.1.1
server=8.8.8.8"

cat > "$bin/nvram" <<'EOS'
#!/bin/sh
case "$2" in
    wrvpn_enabled) echo "3";;
    wrvpn_protect) echo "192.168.20.0/24";;
    wrvpn_use_dns) echo "0";;
    *) exit 1;;
esac
EOS
chmod +x "$bin/nvram"
run stop
test ! -e "$root/dns/wrvpn.servers"

# An id removed from wrvpn_enabled but still present in runtime state is
# stopped once; a "no stored profile" exit is tolerated, not a failure.
mkdir -p "$root/run/7"
cat > "$bin/wr-vpn-profile" <<EOS
#!/bin/sh
echo "ctl \$*" >> "$calls"
case "\$1 \$2" in "down 7") exit 5;; esac
EOS
chmod +x "$bin/wr-vpn-profile"
cat > "$bin/nvram" <<'EOS'
#!/bin/sh
case "$2" in
    wrvpn_enabled) echo "3";;
    wrvpn_protect) echo "192.168.20.0/24";;
    *) exit 1;;
esac
EOS
chmod +x "$bin/nvram"
: > "$calls"
if run stop 2>/dev/null; then :; else
    echo 'an absent stored profile was reported as a stop failure' >&2
    exit 1
fi
test "$(cat "$calls")" = "ctl down 3
ctl down 7"

rm -rf "$root"
echo 'PASS VPN profile service: up/down/status argument passing, protected prefixes, invalid id refusal, opt-in DNS aggregation and removal, runtime-only id teardown'
