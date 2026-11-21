# Sourced by check-stubby-config.sh and check-stubby-runtime.sh after setting
# $here. Builds a scratch copy of the shipped stubby.sh with router paths
# redirected and router commands stubbed, and defines generate().
#
# The stubbed stubby validates fixture-style (copy, exit STUBBY_CHECK_STATUS)
# unless STUBBY_REAL names a real command, e.g. the image binary under QEMU.
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/storage" "$work/share" "$work/run"

cat > "$work/bin/nvram" <<'EOF'
#!/bin/sh
[ "$1" = get ] || exit 1
grep "^$2=" "$NVRAM_FILE" | head -n 1 | cut -d= -f2-
EOF
cat > "$work/bin/logger" <<'EOF'
#!/bin/sh
[ "$1" = -t ] && shift 2
printf '%s\n' "$*" >> "$LOG_FILE"
EOF
cat > "$work/bin/stubby" <<'EOF'
#!/bin/sh
# STUBBY_REAL is a command line; word splitting is intended.
[ -n "${STUBBY_REAL:-}" ] && exec $STUBBY_REAL "$@"
[ "$1" = -C ] && [ "$3" = -i ] || exit 64
cp "$2" "$CHECKED_FILE"
exit "${STUBBY_CHECK_STATUS:-0}"
EOF
chmod +x "$work/bin/nvram" "$work/bin/logger" "$work/bin/stubby"
: > "$work/share/ca.crt"

# Library copy: router paths redirected, lifecycle dispatch removed.
lib="$work/stubby-lib.sh"
sed -e "s|^STUBBY_BIN=/usr/sbin/stubby\$|STUBBY_BIN=$work/bin/stubby|" \
    -e "s|^STUBBY_CONFIG=/etc/storage/stubby/stubby.yml\$|STUBBY_CONFIG=$work/storage/stubby/stubby.yml|" \
    -e "s|^PID_FILE=/var/run/stubby.pid\$|PID_FILE=$work/run/stubby.pid|" \
    -e "s|^CA_FILE=/usr/share/stubby/ca-certificates.crt\$|CA_FILE=\${TEST_CA_FILE}|" \
    -e "s|^DNS_LISTENER_GUARD=/usr/bin/stubby-dns-listener-guard.sh\$|DNS_LISTENER_GUARD=$here/../dns-common/dns-listener-guard.sh|" \
    -e "s|/etc/storage/stubby|$work/storage/stubby|g" \
    -e '/^# One lock covers the entire restart/,$d' \
    "$here/stubby.sh" > "$lib"
for expected in "STUBBY_BIN=$work/bin/stubby" "STUBBY_CONFIG=$work/storage/stubby/stubby.yml" \
    'CA_FILE=${TEST_CA_FILE}' "mktemp -d $work/storage/stubby/.stubby.XXXXXX"; do
    grep -qF "$expected" "$lib" || { echo "FAIL stubby.sh layout changed; cannot redirect: $expected"; exit 1; }
done
if grep -qE '/etc/storage|^exec 9>|^case "\$1"' "$lib"; then
    echo 'FAIL stubby.sh layout changed; router paths or dispatch remain in the test copy'
    exit 1
fi

# generate NVRAM [CHECK_STATUS] [CA_FILE]: sets status, config and messages.
generate()
{
    printf '%s\n' "$1" > "$work/nvram"
    : > "$work/log"
    rm -f "$work/checked.yml"
    (
        PATH="$work/bin:$PATH" NVRAM_FILE="$work/nvram" LOG_FILE="$work/log" \
        CHECKED_FILE="$work/checked.yml" STUBBY_CHECK_STATUS="${2:-0}" \
        TEST_CA_FILE="${3:-$work/share/ca.crt}"
        export PATH NVRAM_FILE LOG_FILE CHECKED_FILE STUBBY_CHECK_STATUS TEST_CA_FILE
        if [ -n "${STUBBY_IMAGE_SHELL:-}" ]; then
            # Explicit runner: image shell executes the real configuration code.
            # Fixture commands remain host stubs; this is not a boot/lifecycle test.
            "$STUBBY_IMAGE_SHELL" -c '. "$1"; make_config' sh "$lib"
        else
            . "$lib"
            make_config
        fi
    ) 2>> "$work/log"
    status=$?
    config="$work/storage/stubby/stubby.yml"
    messages=$(cat "$work/log")
}
