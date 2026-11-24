#!/bin/sh
# Refresh configured HTTPS feeds for the Classic-managed namespace.
set -eu
umask 077
config=${1:-/etc/storage/wr-classic-ipset.feeds}
apply=${WR_CLASSIC_IPSET_APPLY:-/usr/sbin/wr-classic-ipset-apply}
curl=${WR_CLASSIC_IPSET_CURL:-/usr/bin/curl}
status=${WR_CLASSIC_IPSET_STATUS:-/var/run/wr-classic-ipset.status}
write_status() {
    tmp=$(mktemp "${status}.XXXXXX") || return 1
    if ! printf '%s %s %s\n' "$1" "$2" "$3" >"$tmp" || ! mv -f "$tmp" "$status"; then
        rm -f "$tmp"
        return 1
    fi
}

if [ ! -e "$config" ]; then
    write_status unconfigured 0 0
    exit
fi
if [ ! -f "$config" ] || [ "$(wc -c <"$config")" -gt 8192 ]; then
    write_status error 0 0
    exit 1
fi

work=$(mktemp -d)
cleanup() {
    rm -f "$work/feeds" "$work/list"
    rmdir "$work"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

awk '
    /^[[:space:]]*(#|$)/ { next }
    {
        if (++count > 16 || NF != 2 || length($1) > 20 ||
            $1 !~ /^[A-Za-z0-9_]+$/ || $1 == "zapret2_clients" || seen[$1]++ ||
            $2 !~ /^https:\/\/[^[:cntrl:][:space:]]+$/)
            exit 1
        print $1, $2
    }
' "$config" >"$work/feeds" || {
    echo "Invalid IPSet feed configuration" >&2
    write_status error 0 0
    exit 1
}

updated=0
failed=0
while read -r name url; do
    if ! (
        # Bound storage even when curl cannot infer the response length.
        ulimit -f 32
        "$curl" --disable --fail --silent --show-error --proto '=https' \
            --connect-timeout 5 --max-time 20 --max-filesize 16384 \
            --output "$work/list" -- "$url"
    ) || [ ! -s "$work/list" ] || ! WR_CLASSIC_IPSET_REQUIRE_ENTRIES=1 "$apply" "$work/list" "$name"; then
        echo "IPSet refresh failed for $name" >&2
        failed=$((failed + 1))
    else
        updated=$((updated + 1))
    fi
    rm -f "$work/list"
done <"$work/feeds"
if [ "$failed" -gt 0 ]; then
    write_status error "$updated" "$failed"
    exit 1
fi
if [ "$updated" -eq 0 ]; then
    write_status unconfigured 0 0
else
    write_status updated "$updated" 0
    hook="$(dirname "$config")/wr-classic-ipset.post.sh"
    if [ ! -L "$hook" ] && [ -f "$hook" ] && [ -s "$hook" ] &&
       [ "$(wc -c <"$hook")" -le 8192 ]; then
        /bin/sh "$hook" </dev/null || {
            echo "IPSet post-update script failed" >&2
            exit 1
        }
    fi
fi
