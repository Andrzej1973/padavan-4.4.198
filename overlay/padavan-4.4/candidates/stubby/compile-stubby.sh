#!/bin/bash
# Standalone MIPS compile proof, not a router installation.
set -euo pipefail
: "${TARGET_CC:?Absolute target compiler required}"
: "${TARGET_STAGE:?Absolute firmware dependency stage required}"
: "${STUBBY_CANDIDATE_DIR:?Absolute candidate work directory required}"
test -x "$TARGET_CC"
test -f "$TARGET_STAGE/include/openssl/ssl.h"
test -f "$TARGET_STAGE/lib/libssl.so"
test -f "$TARGET_STAGE/lib/libcrypto.so"
cross="${TARGET_CC%gcc}"
mkdir -p "$STUBBY_CANDIDATE_DIR"
cd "$STUBBY_CANDIDATE_DIR"
curl --fail --location --retry 3 -o yaml-0.2.5.tar.gz \
  https://github.com/yaml/libyaml/releases/download/0.2.5/yaml-0.2.5.tar.gz
echo 'c642ae9b75fee120b2d96c712538bd2cf283228d2337df2cf2988e3c02678ef4  yaml-0.2.5.tar.gz' | sha256sum -c -
tar xzf yaml-0.2.5.tar.gz
cd yaml-0.2.5
CC="$TARGET_CC" AR="${cross}ar" RANLIB="${cross}ranlib" \
CFLAGS='-O2 -fPIC -mips32r2' \
./configure --host=mipsel-linux-uclibc --build="$(gcc -dumpmachine)" \
  --prefix=/ --libdir=/lib --includedir=/include --disable-shared --enable-static \
  2>&1 | tee ../yaml-configure.log
make -j2 2>&1 | tee ../yaml-compile.log
make install DESTDIR="$STUBBY_CANDIDATE_DIR/yaml-stage"
cd "$STUBBY_CANDIDATE_DIR"
curl --fail --location --retry 3 -o getdns-1.7.3.tar.gz \
  https://getdnsapi.net/dist/getdns-1.7.3.tar.gz
echo 'f1404ca250f02e37a118aa00cf0ec2cbe11896e060c6d369c6761baea7d55a2c  getdns-1.7.3.tar.gz' | sha256sum -c -
tar xzf getdns-1.7.3.tar.gz
test -f getdns-1.7.3/stubby/CMakeLists.txt
sysroot="$($TARGET_CC -print-sysroot)"
PKG_CONFIG_PATH= \
PKG_CONFIG_LIBDIR="$STUBBY_CANDIDATE_DIR/yaml-stage/lib/pkgconfig" \
PKG_CONFIG_SYSROOT_DIR="$STUBBY_CANDIDATE_DIR/yaml-stage" \
cmake -S getdns-1.7.3 -B build \
  -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=mipsel \
  -DCMAKE_C_COMPILER="$TARGET_CC" \
  -DCMAKE_FIND_ROOT_PATH="$TARGET_STAGE;$STUBBY_CANDIDATE_DIR/yaml-stage;$sysroot" \
  -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
  -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
  -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
  -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY \
  -DCMAKE_C_FLAGS_RELEASE='-O2 -DNDEBUG -mips32r2' \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,$TARGET_STAGE/lib" \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_INSTALL_FULL_SYSCONFDIR=/etc/storage \
  -DCMAKE_INSTALL_SYSCONFDIR=/etc/storage \
  -DCMAKE_INSTALL_FULL_RUNSTATEDIR=/var/run \
  -DOPENSSL_INCLUDE_DIR="$TARGET_STAGE/include" \
  -DOPENSSL_SSL_LIBRARY="$TARGET_STAGE/lib/libssl.so" \
  -DOPENSSL_CRYPTO_LIBRARY="$TARGET_STAGE/lib/libcrypto.so" \
  -DUSE_LIBIDN2=OFF -DENABLE_UNBOUND_EVENT_API=OFF -DENABLE_STUB_ONLY=ON \
  -DBUILD_GETDNS_QUERY=OFF -DBUILD_GETDNS_SERVER_MON=OFF \
  -DBUILD_STUBBY=ON -DBUILD_EXAMPLES=OFF \
  -DENABLE_STATIC=ON -DENABLE_SHARED=OFF -DBUILD_TESTING=OFF \
  -DCMAKE_BUILD_TYPE=Release 2>&1 | tee getdns-configure.log
cmake --build build --parallel 2 2>&1 | tee getdns-compile.log
binary="$(find build -type f -name stubby -print -quit)"
test -n "$binary"
readelf -h "$binary" > elf-header.txt
grep -q 'Machine:.*MIPS' elf-header.txt
readelf -d "$binary" > elf-dependencies.txt
cp "$binary" stubby-mips
# Execution and TLS queries require the actual target; never run it on x86.
