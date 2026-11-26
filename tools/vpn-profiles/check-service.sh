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
cat > "$bin/flock" <<'EOS'
#!/bin/sh
exit 0
EOS
chmod +x "$bin/nvram" "$bin/wr-vpn-profile" "$bin/logger" "$bin/flock"
cat > "$bin/killall" <<EOS
#!/bin/sh
printf '%s\n' "\$*" >> "$root/dns-signals"
EOS
chmod +x "$bin/killall"

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
    wrvpn_enabled) echo "3,5";;
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
test "$(stat -c '%a' "$root/dns/wrvpn.servers")" = 644

cat > "$bin/wr-vpn-profile" <<EOS
#!/bin/sh
echo "ctl \$*" >> "$calls"
case "\$1 \$2" in "up 5") exit 9;; esac
EOS
printf 'server=192.0.2.53\n' > "$root/dns/wrvpn.servers"
: > "$calls"
if run start 2>/dev/null; then
    echo 'partial start was reported as success' >&2
    exit 1
fi
test "$(cat "$calls")" = "ctl up 3 192.168.20.0/24
ctl up 5 192.168.20.0/24"
test "$(cat "$root/dns/wrvpn.servers")" = "server=1.1.1.1
server=8.8.8.8"

# The UI's detached up/down worker calls this locked reconciliation command.
: > "$root/run/3/wrv3.dns"
printf '2001:db8::53\n' > "$root/run/3/wrv3.dns"
: > "$calls"
: > "$root/dns-signals"
run dns-sync
test "$(cat "$root/dns-signals")" = '-HUP dnsmasq'
test "$(cat "$root/dns/wrvpn.servers")" = "server=2001:db8::53"

# A symlink in runtime state is refused and leaves the previous resolver file.
printf '192.0.2.53\n' > "$root/foreign-dns"
rm -f "$root/run/3/wrv3.dns"
ln -s "$root/foreign-dns" "$root/run/3/wrv3.dns"
if run dns-sync 2>/dev/null; then
    echo 'symlinked per-profile DNS file was accepted' >&2
    exit 1
fi
test "$(cat "$root/dns-signals")" = '-HUP dnsmasq'
test "$(cat "$root/dns/wrvpn.servers")" = "server=2001:db8::53"
rm -f "$root/run/3/wrv3.dns"

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
test -f "$root/dns/wrvpn.servers"
test ! -s "$root/dns/wrvpn.servers"

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

cat > "$bin/wr-vpn-profile" <<EOS
#!/bin/sh
echo "ctl \$*" >> "$calls"
case "\$1 \$2" in "down 3") exit 9;; esac
EOS
printf 'server=192.0.2.53\n' > "$root/dns/wrvpn.servers"
: > "$calls"
if run stop 2>/dev/null; then
    echo 'partial stop was reported as success' >&2
    exit 1
fi
test "$(cat "$calls")" = "ctl down 3
ctl down 7"
test ! -s "$root/dns/wrvpn.servers"

# The profile manager must not run without its lifecycle lock utility.
mkdir -p "$root/no-flock"
: > "$calls"
if PATH="$root/no-flock" WRVPN_CTL="$bin/wr-vpn-profile" \
    WRVPN_LOCK="$root/no-flock.lock" WRVPN_DNS_DIR="$root/dns" \
    WRVPN_RUN_DIR="$root/run" "$here/service.sh" start 2>/dev/null; then
    echo 'missing flock was accepted' >&2
    exit 1
fi
test ! -s "$calls"

rm -rf "$root"
echo 'PASS VPN profile service: start lock enforcement, up/down/status, protected prefixes, invalid id refusal, opt-in DNS aggregation/removal and runtime-only teardown'
