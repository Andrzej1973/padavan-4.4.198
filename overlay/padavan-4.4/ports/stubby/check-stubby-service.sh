#!/bin/sh
# Run the shipped stubby.sh lifecycle inside the image ROMFS.
#
#   sudo check-stubby-service.sh ROMFS [SETTINGS]
#
# A copy of ROMFS becomes a chroot, so stubby.sh runs under the image's own
# busybox shell and applets, and starts the image's Stubby, all through
# qemu-mipsel binfmt. NVRAM reads come from SETTINGS (default: the strict
# three-resolver runtime-settings.nvram); writes fail. start, restart and stop
# must succeed, and names must resolve through the Stubby that start launched.
# Requires root, qemu-mipsel-static with a registered binfmt handler, dig,
# network access to the resolvers' port 853, and a PID 1 that reaps orphans
# as the router's init does (in Docker: run --init), or a stopped daemon
# lingers as a zombie and stop reports it still running.
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
romfs=${1:-}
settings=${2:-$here/runtime-settings.nvram}
[ -n "$romfs" ] || { echo "Usage: $0 ROMFS [SETTINGS]" >&2; exit 2; }
[ "$(id -u)" -eq 0 ] || { echo 'FAIL root required (chroot and mounts)'; exit 1; }
binfmt=/proc/sys/fs/binfmt_misc/qemu-mipsel
[ -r "$binfmt" ] && grep -qx enabled "$binfmt" ||
    { echo 'FAIL no enabled qemu-mipsel binfmt handler (install qemu-user-static)'; exit 1; }
command -v dig >/dev/null || { echo 'FAIL dig required'; exit 1; }

root=$(mktemp -d) || exit 1
mounted=
cleanup()
{
    for pid in $(chroot "$root" /bin/pidof stubby 2>/dev/null); do kill "$pid" 2>/dev/null; done
    for point in $mounted; do umount "$point" 2>/dev/null; done
    rm -rf "$root"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
failed() { echo "FAIL $*"; exit 1; }

cp -a "$romfs/." "$root/" || failed "cannot copy $romfs"
# Without the fix-binary flag the interpreter path is resolved in the chroot.
interpreter=$(sed -n 's/^interpreter //p' "$binfmt")
if ! grep -q '^flags:.*F' "$binfmt"; then
    mkdir -p "$root$(dirname "$interpreter")" && cp "$interpreter" "$root$interpreter" ||
        failed "cannot install $interpreter in the chroot"
fi
# Image shell script replaces the NVRAM client: reads only, writes refused.
rm -f "$root/usr/sbin/nvram"
cat > "$root/usr/sbin/nvram" <<'EOF'
#!/bin/sh
[ "$1" = get ] || { echo "nvram $1 refused in service test" >&2; exit 1; }
grep "^$2=" /etc/test-nvram | head -n 1 | cut -d= -f2-
EOF
chmod 755 "$root/usr/sbin/nvram"
tr -d '\r' < "$settings" > "$root/etc/test-nvram" || failed "cannot read $settings"
mkdir -p "$root/proc" "$root/dev"
mount -t proc proc "$root/proc" && mounted="$root/proc" || failed 'cannot mount proc'
mount --bind /dev "$root/dev" && mounted="$root/dev $mounted" || failed 'cannot bind /dev'
chroot "$root" /bin/sh -c 'mkdir -p /var/run /var/lock /etc/storage' || failed 'image shell cannot run in the chroot'

port=$(sed -n 's/^stubby_listen_port=//p' "$root/etc/test-nvram")
lifecycle()
{
    # A file, not $(...): the daemon Stubby inherits and keeps the output open.
    timeout 120 chroot "$root" /usr/bin/stubby.sh "$1" > "$root/tmp/lifecycle.log" 2>&1 < /dev/null
    result=$?
    [ "$result" -eq 0 ] || { cat "$root/tmp/lifecycle.log"; failed "stubby.sh $1 exited $result in the image shell"; }
    echo "stubby.sh $1: ok"
}
resolves()
{
    tries=0
    until [ -n "$(dig @127.0.0.1 -p "$port" +time=6 +tries=1 +short "$1" A 2>/dev/null | grep -E '^[0-9.]+$')" ]; do
        tries=$((tries + 1))
        [ "$tries" -lt 10 ] || failed "$1 did not resolve through the service Stubby"
        sleep 2
    done
    echo "Resolved $1 through the started service"
}
service_pid() { chroot "$root" /bin/sh -c 'cat /var/run/stubby.pid 2>/dev/null'; }

lifecycle start
first=$(service_pid)
[ -n "$first" ] && kill -0 "$first" 2>/dev/null || failed 'start left no running Stubby with a pid file'
resolves example.com
lifecycle restart
second=$(service_pid)
[ -n "$second" ] && [ "$second" != "$first" ] && kill -0 "$second" 2>/dev/null ||
    failed 'restart did not replace the running Stubby'
resolves discord.com
lifecycle stop
kill -0 "$second" 2>/dev/null && failed 'stop left Stubby running'
[ -z "$(service_pid)" ] || failed 'stop left the pid file behind'
echo 'PASS stubby.sh start, restart and stop under the image shell; started Stubby resolves names'
