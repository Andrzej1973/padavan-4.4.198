SRC_NAME = pcre2-10.49
SRC_URL = https://github.com/PCRE2Project/pcre2/releases/download/pcre2-10.49/$(SRC_NAME).tar.bz2
SRC_SHA256 = 53c156e1ba416a20da8e65395daa132da0d80e76910424caca3fcdae7831d384

CFLAGS += -fPIC -ffunction-sections -fdata-sections
LDFLAGS += -Wl,--gc-sections

.PHONY: all download_test extract_test config_test configure install romfs clean
all: download_test extract_test config_test
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

download_test:
	test -f $(SRC_NAME).tar.bz2 || wget -t5 --timeout=20 -O $(SRC_NAME).tar.bz2 $(SRC_URL)
	echo "$(SRC_SHA256)  $(SRC_NAME).tar.bz2" | sha256sum -c -

extract_test: download_test
	test -d $(SRC_NAME) || tar xjf $(SRC_NAME).tar.bz2

config_test: extract_test
	test -f config_done || $(MAKE) configure

configure:
	cd $(SRC_NAME) && \
		CC="$(CC)" AR="$(AR)" RANLIB="$(RANLIB)" \
		CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" \
		./configure --prefix=/ --libdir=/lib --includedir=/include \
			--enable-pcre2-8 --disable-pcre2-16 --disable-pcre2-32 \
			--enable-unicode --disable-jit --enable-shared --enable-static \
			--disable-pcre2grep-libz --disable-pcre2grep-libbz2 \
			--host=$(HOST_TARGET) --build=$(HOST_BUILD)
	touch config_done

install: all
	$(MAKE) -C $(SRC_NAME) install DESTDIR="$(STAGEDIR)"

romfs:
	cp -fP $(STAGEDIR)/lib/libpcre2-8.so* $(ROMFSDIR)/lib
	cp -fP $(STAGEDIR)/lib/libpcre2-posix.so* $(ROMFSDIR)/lib

clean:
	@if [ -f $(SRC_NAME)/Makefile ]; then $(MAKE) -C $(SRC_NAME) distclean; fi
	rm -f config_done

