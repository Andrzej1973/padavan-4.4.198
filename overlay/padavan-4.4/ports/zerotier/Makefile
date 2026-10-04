# ZeroTier 1.16.2 source build, verified candidate run 37154558057.
# Upstream revision is immutable; local/owned source mirror is a delivery task.
SRC_NAME := ZeroTierOne-1.16.2
SRC_COMMIT := fe29cd88886e4f58547ba7f740b2d73eb49ab222
SRC_REPOSITORY := https://github.com/zerotier/ZeroTierOne.git
THISDIR := $(shell pwd)
ZT_TOOLCHAIN := $(subst ",,$(CONFIG_CROSS_COMPILER_ROOT))
ZT_CC := $(ZT_TOOLCHAIN)/bin/mipsel-linux-uclibc-gcc
ZT_CROSS := $(ZT_TOOLCHAIN)/bin/mipsel-linux-uclibc-

.PHONY: all source_test clean romfs
all: source_test
	$(MAKE) -C $(SRC_NAME) -j$(HOST_NCPU) zerotier-one \
		CC="$(ZT_CC)" CXX="$(ZT_CROSS)g++" AR="$(ZT_CROSS)ar" \
		ZT_EMBEDDED=1 ZT_SSO_SUPPORTED=0 ZT_NONFREE=0 ZT_CONTROLLER=0 ZT_OTEL=0 \
		MINIUPNPC_IS_NEW_ENOUGH=0 \
		CFLAGS="-O2 -mips32r2 -ffunction-sections -fdata-sections" \
		CXXFLAGS="-O2 -mips32r2 -ffunction-sections -fdata-sections" \
		LDFLAGS="-Wl,--gc-sections -static-libstdc++" LDLIBS="-latomic"

source_test:
	@if [ ! -d "$(SRC_NAME)/.git" ]; then \
		git init "$(SRC_NAME)" && \
		git -C "$(SRC_NAME)" fetch --depth=1 "$(SRC_REPOSITORY)" "$(SRC_COMMIT)" && \
		git -C "$(SRC_NAME)" checkout --detach FETCH_HEAD; \
	fi
	@test "$$(git -C "$(SRC_NAME)" rev-parse HEAD)" = "$(SRC_COMMIT)"
	@expected="$$(sha256sum prepare-source.py | cut -d ' ' -f1)"; \
		if [ -f "$(SRC_NAME)/.padavan-prepared" ]; then \
			test "$$(cat "$(SRC_NAME)/.padavan-prepared")" = "$$expected" || { \
				echo "ZeroTier preparation changed: recreate the source checkout before rebuilding" >&2; exit 1; }; \
		else \
			python3 prepare-source.py "$(SRC_NAME)" && \
			printf '%s\n' "$$expected" > "$(SRC_NAME)/.padavan-prepared"; \
		fi

clean:
	@if [ -f "$(SRC_NAME)/make-linux.mk" ]; then \
		$(MAKE) -C "$(SRC_NAME)" clean; \
	fi

romfs:
	$(ROMFSINST) -p +x $(THISDIR)/$(SRC_NAME)/zerotier-one /usr/bin/zerotier-one
	$(ROMFSINST) -p +x $(THISDIR)/zerotier.sh /usr/bin/zerotier.sh
	ln -sf zerotier-one $(ROMFSDIR)/usr/bin/zerotier-cli
	ln -sf zerotier-one $(ROMFSDIR)/usr/bin/zerotier-idtool
	@library="$$($(ZT_CC) -print-file-name=libatomic.so.1)"; \
		test "$$library" != "libatomic.so.1" && test -s "$$library" && \
		$(ROMFSINST) -p +x "$$(readlink -f "$$library")" /lib/libatomic.so.1

