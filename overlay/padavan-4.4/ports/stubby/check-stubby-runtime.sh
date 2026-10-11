#!/bin/sh
# Resolve real names over DNS-over-TLS through the image's own Stubby.
#
#   check-stubby-runtime.sh ROMFS [SETTINGS] [--outage]
#
# stubby.sh generates the configuration from SETTINGS (default: the strict
# three-resolver runtime-settings.nvram), the image binary validates it under
# qemu-mipsel with the image's loader, libraries and CA bundle, and dig then
# queries the running daemon. Requires network access to the resolvers' port
# 853. --outage also blocks tcp/853 (root or passwordless sudo, iptables):
# strict mode must answer SERVFAIL, then recover once the block is lifted.
#
# Covers binary, OpenSSL, CA and configuration. A router's boot clock, rc
# startup order and hardware are not emulated.
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
romfs=
settings=$here/runtime-settings.nvram
outage=0
for arg; do
    case "$arg" in
        --outage) outage=1;;
        *) if [ -z "$romfs" ]; then romfs=$arg; else settings=$arg; fi;;
    esac
done
[ -n "$romfs" ] || { echo "Usage: $0 ROMFS [SETTINGS] [--outage]" >&2; exit 2; }
romfs=$(CDPATH= cd -- "$romfs" && pwd) || exit 1
for path in usr/sbin/stubby usr/share/stubby/ca-certificates.crt lib/ld-uClibc.so.0; do
    [ -e "$romfs/$path" ] || { echo "FAIL image file missing: /$path"; exit 1; }
done
qemu=$(command -v qemu-mipsel-static || command -v qemu-mipsel) || { echo 'FAIL qemu-mipsel(-static) required'; exit 1; }
command -v dig >/dev/null || { echo 'FAIL dig required'; exit 1; }

# Execute shell compatibility checks with the image shell, not the host shell.
# This catches missing builtins; full service lifecycle tests remain separate.
[ -f "$romfs/bin/busybox" ] || { echo 'FAIL image BusyBox missing'; exit 1; }
"$qemu" -L "$romfs" "$romfs/bin/busybox" sh -c 'type type >/dev/null' ||
    { echo 'FAIL image shell lacks the dependency-check builtin'; exit 1; }
for pair in "stubby.sh:usr/bin/stubby.sh" "../privoxy/privoxy.sh:usr/bin/privoxy.sh" "../zerotier/firewall-policy.sh:usr/bin/zerotier-policy.sh"; do
    source_script="$here/${pair%%:*}"
    script="$romfs/${pair#*:}"
    [ -f "$script" ] && [ -x "$script" ] ||
        { echo "FAIL shipped service script missing or not executable: $script"; exit 1; }
    cmp -s "$source_script" "$script" ||
        { echo "FAIL shipped service script differs from tested source: $script"; exit 1; }
    "$qemu" -L "$romfs" "$romfs/bin/busybox" sh -n "$script" ||
        { echo "FAIL image shell rejects $script"; exit 1; }
    if grep -Eq 'command[[:space:]]+-v' "$script"; then
        "$qemu" -L "$romfs" "$romfs/bin/busybox" sh -c 'command -v type >/dev/null' ||
            { echo "FAIL unsupported command -v dependency check in $script"; exit 1; }
    fi
done
echo 'PASS image BusyBox builtin and three service-script syntax checks'

. "$here/stubby-test-env.sh"
STUBBY_REAL="$qemu -L $romfs $romfs/usr/sbin/stubby"
export STUBBY_REAL
# The configuration functions must also run in the shipped MIPS shell.
STUBBY_IMAGE_SHELL="$work/image-shell"
cat > "$STUBBY_IMAGE_SHELL" <<EOF
#!/bin/sh
exec "$qemu" -L "$romfs" "$romfs/bin/busybox" sh "\$@"
EOF
chmod +x "$STUBBY_IMAGE_SHELL"
export STUBBY_IMAGE_SHELL

daemon=
blocked=0
as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo -n "$@"; fi; }
block() { as_root iptables -A OUTPUT -p tcp --dport 853 -j REJECT --reject-with tcp-reset && blocked=1; }
unblock() { [ "$blocked" -eq 0 ] || { as_root iptables -D OUTPUT -p tcp --dport 853 -j REJECT --reject-with tcp-reset; blocked=0; }; }
cleanup()
{
    unblock
    [ -n "$daemon" ] && kill "$daemon" 2>/dev/null
    rm -rf "$work"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

failed() { echo "FAIL $*"; echo '--- stubby log (last 30 lines)'; tail -n 30 "$work/stubby.log" 2>/dev/null; exit 1; }

# Configuration exactly as the router builds it, validated by the image binary.
generate "$(tr -d '\r' < "$settings")" 0 "$romfs/usr/share/stubby/ca-certificates.crt"
[ "$status" -eq 0 ] || { echo 'FAIL stubby.sh or the image binary rejected the configuration:'; printf '  %s\n' "$messages"; exit 1; }
listen=$(sed -n 's/^  - "\(.*\)@\([0-9]*\)"$/\1 \2/p' "$config" | head -n 1)
address=${listen% *} port=${listen#* }
[ "$address" = 0.0.0.0 ] && address=127.0.0.1
[ -n "$port" ] || failed 'no listen address in generated configuration'
echo "Generated and image-validated configuration; listening on $address:$port"

$STUBBY_REAL -C "$config" -l -v 7 > "$work/stubby.log" 2>&1 &
daemon=$!

# status NAME: prints the dig status (or "no answer") within one try.
status_of()
{
    dig @"$address" -p "$port" +time=6 +tries=1 "$1" A 2>&1 |
        sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -n 1 | grep . || echo 'no answer'
}

tries=0
until [ "$(status_of example.com)" != 'no answer' ]; do
    kill -0 "$daemon" 2>/dev/null || failed 'stubby exited during startup'
    tries=$((tries + 1))
    [ "$tries" -lt 10 ] || failed 'stubby did not answer after 10 attempts'
    sleep 2
done

for name in google.com discord.com example.com; do
    for attempt in 1 2 3; do
        answer=$(dig @"$address" -p "$port" +time=6 +tries=1 +short "$name" A 2>/dev/null | grep -E '^[0-9.]+$' | head -n 1)
        [ -n "$answer" ] && break
    done
    [ -n "$answer" ] || failed "$name did not resolve through Stubby (status: $(status_of "$name"))"
    echo "Resolved $name -> $answer"
done
grep -q 'Verify passed : TLS' "$work/stubby.log" || failed 'no authenticated TLS session in the stubby log'
echo 'Authenticated DNS-over-TLS confirmed in the stubby log'

if [ "$outage" -eq 1 ]; then
    block || failed 'cannot block tcp/853 (needs root or passwordless sudo and iptables)'
    # Fresh names avoid Stubby's answer cache.
    result=$(status_of "outage-$(date +%s).example.org")
    [ "$result" = SERVFAIL ] || failed "strict Stubby answered $result while DNS-over-TLS was unreachable"
    echo 'Strict mode answered SERVFAIL while tcp/853 was blocked'
    unblock
    start=$(date +%s)
    # A name not resolved before, so no cached answer can stand in for recovery.
    until [ -n "$(dig @"$address" -p "$port" +time=6 +tries=1 +short wikipedia.org A 2>/dev/null | grep -E '^[0-9.]+$')" ]; do
        [ $(($(date +%s) - start)) -lt 60 ] || failed 'no recovery within 60 s after tcp/853 was unblocked'
        sleep 2
    done
    echo "Recovered $(($(date +%s) - start)) s after tcp/853 was unblocked"
fi
kill -0 "$daemon" 2>/dev/null || failed 'stubby exited while serving queries'
echo 'PASS image Stubby resolves over authenticated DNS-over-TLS with the stubby.sh configuration'
