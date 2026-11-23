#!/bin/sh
# Replace only the Classic-managed IPv4 set after validating the whole list.
set -eu
umask 077

source=${1:-/etc/storage/wr-classic-ipset.list}
name=${2:-ipv4}
case "$name" in
    ''|*[!a-zA-Z0-9_]*) echo "Invalid managed IPSet name" >&2; exit 1 ;;
esac
[ "${#name}" -le 20 ] || { echo "Managed IPSet name is too long" >&2; exit 1; }
live="wr_classic_$name"
pending="wr_ipset_tmp_$$"
ipset=${WR_CLASSIC_IPSET_BIN:-/sbin/ipset}
work=$(mktemp)
created=0
cleanup() {
    if [ "$created" = 1 ]; then
        "$ipset" destroy "$pending" >/dev/null 2>&1 || :
    fi
    rm -f "$work"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

if [ -e "$source" ]; then
    [ -f "$source" ] && [ "$(wc -c <"$source")" -le 16384 ] || exit 1
    awk '
        { sub(/#.*/, ""); gsub(/^[[:space:]]+|[[:space:]]+$/, "") }
        !length { next }
        {
            if (++count > 512 || $0 !~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(\/[0-9]+)?$/)
                exit 1
            fields = split($0, part, /[.\/]/)
            for (i = 1; i <= fields; i++) {
                if (length(part[i]) > 3 || (length(part[i]) > 1 && part[i] ~ /^0/) ||
                    part[i] + 0 > (i == 5 ? 32 : 255))
                    exit 1
            }
            if (fields == 5 && part[5] + 0 == 0) exit 1
            if (!seen[$0]++) print
        }
    ' "$source" >"$work" || { echo "Invalid IPv4 set configuration" >&2; exit 1; }
fi

if [ "${WR_CLASSIC_IPSET_REQUIRE_ENTRIES:-0}" = 1 ] && [ ! -s "$work" ]; then
    echo "IPSet feed contains no IPv4 entries" >&2
    exit 1
fi

"$ipset" create "$pending" hash:net family inet maxelem 512
created=1
while IFS= read -r address; do
    "$ipset" -exist add "$pending" "$address"
done <"$work"
"$ipset" -exist create "$live" hash:net family inet maxelem 512
"$ipset" swap "$pending" "$live"
