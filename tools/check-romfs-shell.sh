#!/bin/sh
# Check every /bin/sh script in an image ROMFS with the image's own shell.
#
#   check-romfs-shell.sh ROMFS
#
# Scripts run on the router under busybox ash, not the build host's shell.
# Each one must parse with that ash (sh -n), and none may use a builtin the
# image ash lacks. Builtin support is probed from the image binary, never
# assumed. Requires qemu-mipsel(-static); no root or binfmt handler.
set -u
romfs=${1:-}
[ -n "$romfs" ] && [ -x "$romfs/bin/busybox" ] || { echo "Usage: $0 ROMFS (with bin/busybox)" >&2; exit 2; }
romfs=$(CDPATH= cd -- "$romfs" && pwd)
qemu=$(command -v qemu-mipsel-static || command -v qemu-mipsel) || { echo 'FAIL qemu-mipsel(-static) required'; exit 1; }
ash() { "$qemu" -L "$romfs" "$romfs/bin/busybox" sh "$@"; }

ash -c 'exit 0' || { echo 'FAIL the image busybox shell does not run under qemu'; exit 1; }
# Builtins host shells always have but a reduced ash may not.
missing=
for builtin in command type local printf; do
    ash -c "$builtin >/dev/null 2>&1; [ \$? -ne 127 ]" || missing="$missing $builtin"
done
echo "Image ash lacks builtins:${missing:- none}"

failures=0
scripts=0
list=$(mktemp) || exit 1
trap 'rm -f "$list"' EXIT
find "$romfs" -type f -size -2M > "$list"
while IFS= read -r file; do
    first=$(head -c 64 "$file" 2>/dev/null | head -n 1)
    case "$first" in '#!/bin/sh'*) ;; *) continue;; esac
    scripts=$((scripts + 1))
    name=${file#"$romfs"}
    if ! errors=$(ash -n "$file" 2>&1); then
        echo "FAIL $name does not parse with the image ash: $errors"
        failures=$((failures + 1))
    fi
    for builtin in $missing; do
        # Command position: line start, after ; & | ( { ! $( or a backquote,
        # or after a compound-command keyword.
        hits=$(grep -nE "(^|[;&|({!\`]|\\\$\(|(^|[[:space:]])(if|then|else|elif|do|while|until))[[:space:]]*$builtin[[:space:]]" "$file" |
            grep -vE '^[0-9]+:[[:space:]]*#')
        if [ -n "$hits" ]; then
            printf 'FAIL %s uses "%s", which the image ash lacks:\n%s\n' "$name" "$builtin" "$hits"
            failures=$((failures + 1))
        fi
    done
done < "$list"
[ "$scripts" -gt 0 ] || { echo "FAIL no /bin/sh scripts found in $romfs"; exit 1; }
if [ "$failures" -ne 0 ]; then
    echo "FAIL $failures problem(s) in $scripts image shell scripts"
    exit 1
fi
echo "PASS $scripts image /bin/sh scripts parse with the image ash and use only its builtins"
