# Candidate only: source/build registration and service/UI integration are pending.
SRC_NAME = https_dns_proxy-0ba0525
SRC_ARCHIVE = $(ROOTDIR)/../../sources/archives/$(SRC_NAME).tar.gz
SRC_SHA256 = d3723d0e14612d2d2cab1f64150558a2a9804b54b2108afbb3e08949b4220ba6

.PHONY: all source-check configure romfs
all: configure
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)/build

source-check:
	test -f "$(SRC_ARCHIVE)"
	printf '%s  %s\n' "$(SRC_SHA256)" "$(SRC_ARCHIVE)" | sha256sum -c -

$(SRC_NAME)/.source-ready: $(SRC_ARCHIVE)
	printf '%s  %s\n' "$(SRC_SHA256)" "$(SRC_ARCHIVE)" | sha256sum -c -
	mkdir -p $(SRC_NAME)
	tar -xzf "$(SRC_ARCHIVE)" --strip-components=1 -C $(SRC_NAME)
	test -f $(SRC_NAME)/LICENSE
	test -f $(SRC_NAME)/CMakeLists.txt
	touch $@

configure: source-check $(SRC_NAME)/.source-ready
	test -f "$(STAGEDIR)/include/ares.h"
	test -f "$(STAGEDIR)/include/ev.h"
	test -f "$(STAGEDIR)/include/curl/curl.h"
	test -f "$(CONFIG_CMAKE_TOOLCHAIN_FILE)"
	cmake -S $(SRC_NAME) -B $(SRC_NAME)/build \
		-DCMAKE_TOOLCHAIN_FILE="$(CONFIG_CMAKE_TOOLCHAIN_FILE)" \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS_RELEASE="-O2" \
		-DCMAKE_C_FLAGS="$(CFLAGS)" \
		-DCMAKE_EXE_LINKER_FLAGS="$(LDFLAGS) -Wl,-rpath-link,$(STAGEDIR)/lib" \
		-DLIBCARES_INCLUDE_DIR="$(STAGEDIR)/include" \
		-DLIBEV_INCLUDE_DIR="$(STAGEDIR)/include" \
		-DCUSTOM_LIBCURL_INSTALL_PATH="$(STAGEDIR)" \
		-DCMAKE_INSTALL_PREFIX=/usr -DSW_VERSION=donor-archive-d3723d0e \
		-DGIT_EXECUTABLE= -DUSE_CLANG_TIDY=OFF -DHAVE_SD_DAEMON_H=0

romfs:
	$(ROMFSINST) $(SRC_NAME)/build/https_dns_proxy /usr/sbin/https_dns_proxy
