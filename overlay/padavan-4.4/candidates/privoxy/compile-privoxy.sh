#!/bin/sh
# Run on the Linux builder after PCRE2 and firmware dependencies are staged.
# This produces a compile candidate, not an installed router service.
set -eu
: "${PRIVOXY_CANDIDATE_DIR:?Set an absolute candidate work directory}"
: "${TARGET_CC:?Set the absolute MIPS compiler path}"
: "${TARGET_STAGE:?Set the firmware dependency stage directory}"
: "${PCRE2_STAGE:?Set the PCRE2 candidate stage directory}"
: "${TARGET_CFLAGS:?Set project performance compiler flags}"
test -x "$TARGET_CC"
test -f "$PCRE2_STAGE/include/pcre2.h"
test -f "$PCRE2_STAGE/lib/libpcre2-posix.so"
mkdir -p "$PRIVOXY_CANDIDATE_DIR"
cd "$PRIVOXY_CANDIDATE_DIR"
archive=privoxy-4.2.0-stable-src.tar.gz
curl --fail --location --retry 3 --output "$archive" \
  'https://www.privoxy.org/sf-download-mirror/Sources/4.2.0%20%28stable%29/privoxy-4.2.0-stable-src.tar.gz'
echo "6f91267f81f626c416994db89ab62f4d09246eebf4754b81186e13a18ee9028f  $archive" | sha256sum -c -
tar xzf "$archive"
cd privoxy-4.2.0-stable
autoheader
autoconf
CC="$TARGET_CC" \
CFLAGS="$TARGET_CFLAGS" \
CPPFLAGS="-I$PCRE2_STAGE/include -I$TARGET_STAGE/include" \
LDFLAGS="-L$PCRE2_STAGE/lib -L$TARGET_STAGE/lib -Wl,-rpath-link,$PCRE2_STAGE/lib -Wl,-rpath-link,$TARGET_STAGE/lib" \
PKG_CONFIG_PATH= \
PKG_CONFIG_LIBDIR="$PCRE2_STAGE/lib/pkgconfig:$TARGET_STAGE/lib/pkgconfig" \
./configure --host=mipsel-linux-uclibc --build="$(gcc -dumpmachine)" \
  --prefix=/usr --sysconfdir=/etc/storage/privoxy \
  --disable-pcre-jit-compilation \
  --without-openssl --without-mbedtls --without-wolfssl \
  > ../configure.log 2>&1 || { cat ../configure.log; exit 1; }
cat ../configure.log
make -j2 > ../compile.log 2>&1 || { cat ../compile.log; exit 1; }
cat ../compile.log
readelf -h privoxy > ../elf-header.txt
grep -q 'Machine:.*MIPS' ../elf-header.txt
readelf -d privoxy > ../elf-dependencies.txt
# No target executable is run on the x86 builder.
