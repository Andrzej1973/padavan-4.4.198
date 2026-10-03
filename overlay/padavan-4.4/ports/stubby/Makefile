# Stubby 0.4.3 bundled in the official getdns 1.7.3 release.
# Candidate package: runtime/backend/UI integration remains separate.

SRC_NAME = getdns-1.7.3
SRC_URL = https://getdnsapi.net/dist/$(SRC_NAME).tar.gz
SRC_SHA256 = f1404ca250f02e37a118aa00cf0ec2cbe11896e060c6d369c6761baea7d55a2c

.PHONY: all download_test extract_test config_test configure clean install romfs

# Use the compiler and dependency stage exported by the 4.4 build.
# The legacy cross-mipsel-linux.cmake is absent from this source base.
TARGET_STAGE = $(abspath $(STAGEDIR))

CFLAGS += -ffunction-sections -fdata-sections -fvisibility=hidden
LDFLAGS += -Wl,--gc-sections

all: config_test
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)/build

download_test:
	test -f $(SRC_NAME).tar.gz || wget -t5 --timeout=20 -O $(SRC_NAME).tar.gz $(SRC_URL)
	echo "$(SRC_SHA256)  $(SRC_NAME).tar.gz" | sha256sum -c -

extract_test: download_test
	test -d $(SRC_NAME) || tar xzf $(SRC_NAME).tar.gz

config_test: extract_test
	( if [ -f ./config_done ]; then \
		echo "the same configuration"; \
	else \
		$(MAKE) configure && touch config_done; \
	fi )

configure:
	test -f "$(TARGET_STAGE)/include/yaml.h"
	test -f "$(TARGET_STAGE)/lib/libyaml.a"
	test -f "$(TARGET_STAGE)/include/openssl/ssl.h"
	test -f "$(TARGET_STAGE)/lib/libssl.so"
	test -f "$(TARGET_STAGE)/lib/libcrypto.so"
	@target_cc="$(CONFIG_CROSS_COMPILER_PATH)/$(CROSS_COMPILE)gcc" && \
	test -x "$$target_cc" || { echo "Missing target compiler: $$target_cc" >&2; exit 1; }; \
	target_sysroot="$$("$$target_cc" -print-sysroot)" && \
	PKG_CONFIG_PATH= PKG_CONFIG_LIBDIR="$(TARGET_STAGE)/lib/pkgconfig" \
	PKG_CONFIG_SYSROOT_DIR="$(TARGET_STAGE)" \
	cmake -S $(SRC_NAME) -B $(SRC_NAME)/build \
		-DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=mipsel \
		-DCMAKE_C_COMPILER="$$target_cc" \
		-DCMAKE_FIND_ROOT_PATH="$(TARGET_STAGE);$$target_sysroot" \
		-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
		-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
		-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
		-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY \
		-DCMAKE_C_FLAGS_RELEASE="$(CFLAGS) -DNDEBUG" \
		-DCMAKE_EXE_LINKER_FLAGS="$(LDFLAGS) -Wl,-rpath-link,$(TARGET_STAGE)/lib" \
		-DOPENSSL_INCLUDE_DIR="$(TARGET_STAGE)/include" \
		-DOPENSSL_SSL_LIBRARY="$(TARGET_STAGE)/lib/libssl.so" \
		-DOPENSSL_CRYPTO_LIBRARY="$(TARGET_STAGE)/lib/libcrypto.so" \
		-DCMAKE_INSTALL_PREFIX:PATH=/usr \
		-DCMAKE_INSTALL_FULL_SYSCONFDIR=/etc/storage \
		-DCMAKE_INSTALL_SYSCONFDIR=/etc/storage \
		-DCMAKE_INSTALL_FULL_RUNSTATEDIR=/var/run \
		-DENABLE_SYSTEMD=OFF \
		-DUSE_LIBIDN2=OFF \
		-DENABLE_UNBOUND_EVENT_API=OFF \
		-DENABLE_STUB_ONLY=ON \
		-DBUILD_GETDNS_QUERY=OFF \
		-DBUILD_GETDNS_SERVER_MON=OFF \
		-DBUILD_STUBBY=ON \
		-DBUILD_EXAMPLES=OFF \
		-DENABLE_STATIC=ON \
		-DENABLE_SHARED=OFF \
		-DBUILD_TESTING=OFF \
		-DCMAKE_BUILD_TYPE=Release

clean:
	if [ -d $(SRC_NAME)/build ]; then \
		rm -rf $(SRC_NAME)/build; \
	fi; \
	rm -f config_done

install: all
	# The final firmware uses explicit ROMFS copies, never upstream config install.

romfs:
	$(ROMFSINST) $(SRC_NAME)/build/stubby/stubby /usr/sbin/stubby
	$(ROMFSINST) -p +x /usr/bin/stubby.sh
	$(ROMFSINST) -d /www/dot.json
	$(ROMFSINST) -d -S -p 644 cacert-2026-09-25.pem /usr/share/stubby/ca-certificates.crt

