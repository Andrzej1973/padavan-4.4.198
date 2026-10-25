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

ZLIB_H=$(find "$TREE/trunk" -name zlib.h -print -quit 2>/dev/null || true)
[ -n "$ZLIB_H" ] || { echo "zlib.h not found in the Padavan tree" >&2; exit 2; }
ZLIB_INC=$(dirname "$ZLIB_H")

mkdir -p "$BUILD/compat/sys"
printf '#include <linux/capability.h>\n' > "$BUILD/compat/sys/capability.h"

INC="-I$BUILD/compat -I$ZLIB_INC -I$BUILD/libmnl-1.0.5/include -I$BUILD/libnfnetlink-1.0.2/include -I$BUILD/libnetfilter_queue-1.0.5/include"
mkdir -p "$BUILD/obj"

for f in "$BUILD"/libmnl-1.0.5/src/*.c "$BUILD"/libnfnetlink-1.0.2/src/*.c "$BUILD"/libnetfilter_queue-1.0.5/src/*.c; do
    obj="$BUILD/obj/$(basename "$f" .c).o"
    # shellcheck disable=SC2086
    $CC ${CFLAGS:-} -Os -fno-strict-aliasing $INC -c "$f" -o "$obj"
done

# Lua 5.1 ships as sources in the pinned tree; embed it so the package does not
# depend on the lua51 package having been built first.
LUA_DIR="$TREE/trunk/user/lua51/lua-5.1.5/src"
[ -f "$LUA_DIR/lua.h" ] || { echo "lua.h not found at $LUA_DIR" >&2; exit 2; }
LUA_SRC=$(ls "$LUA_DIR"/*.c | grep -v -E '/(lua|luac)\.c$')

# shellcheck disable=SC2086
$CC ${CFLAGS:-} -std=gnu99 -Os $INC -I"$LUA_DIR" \
    -o "$OUT" "$SRC"/*.c "$SRC"/crypto/*.c $LUA_SRC "$BUILD"/obj/*.o \
    -lz -lm ${LDFLAGS:-}

echo "PASS built $OUT"
