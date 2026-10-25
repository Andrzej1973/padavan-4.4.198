#!/bin/sh
# Build nfqws2 for the Padavan MIPS target with the pinned dependency sources.
# Usage: build-nfqws2.sh <padavan-tree> <output-binary>
# Requires CC, CFLAGS and LDFLAGS from the cross build environment.
set -eu

TREE=${1:?padavan tree}
OUT=${2:?output binary}
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPS=${3:-$HERE/../../third_party/netfilter}
SRC="$TREE/trunk/user/zapret2/nfq2"

[ -d "$SRC" ] || { echo "missing nfq2 sources at $SRC" >&2; exit 2; }
[ -n "${CC:-}" ] || { echo "CC is not set" >&2; exit 2; }

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT

for pkg in libmnl-1.0.5 libnfnetlink-1.0.2 libnetfilter_queue-1.0.5; do
    tar -xjf "$DEPS/$pkg.tar.bz2" -C "$BUILD"
done

# These headers normally come from autotools. Only HAVE_VISIBILITY_HIDDEN is
# consulted, so an empty file is a valid build configuration for static use.
for pkg in libmnl-1.0.5 libnetfilter_queue-1.0.5; do
    : > "$BUILD/$pkg/src/config.h"
done

INC="-I$BUILD/libmnl-1.0.5/include -I$BUILD/libnfnetlink-1.0.2/include -I$BUILD/libnetfilter_queue-1.0.5/include"
mkdir -p "$BUILD/obj"

for f in "$BUILD"/libmnl-1.0.5/src/*.c "$BUILD"/libnfnetlink-1.0.2/src/*.c "$BUILD"/libnetfilter_queue-1.0.5/src/*.c; do
    obj="$BUILD/obj/$(basename "$f" .c).o"
    # shellcheck disable=SC2086
    $CC ${CFLAGS:-} -Os -fno-strict-aliasing $INC -c "$f" -o "$obj"
done

LUA_H=$(find "$TREE/trunk/user" -name lua.h -print -quit 2>/dev/null || true)
[ -n "$LUA_H" ] || { echo "lua.h not found in the Padavan tree" >&2; exit 2; }
LUA_INC=$(dirname "$LUA_H")

LUA_LIB=$(find "$TREE/trunk/user" \( -name 'liblua*.a' -o -name 'liblua*.so' -o -name 'liblua*.so.*' \) -print -quit 2>/dev/null || true)
[ -n "$LUA_LIB" ] || { echo "liblua not found in the Padavan tree" >&2; exit 2; }

# shellcheck disable=SC2086
$CC ${CFLAGS:-} -std=gnu99 -Os -I"$LUA_INC" \
    -o "$OUT" "$SRC"/*.c "$SRC"/crypto/*.c "$BUILD"/obj/*.o \
    "$LUA_LIB" -lz -lm ${LDFLAGS:-}

echo "PASS built $OUT"
