SRC_NAME = privoxy-4.2.0-stable
SRC_ARCHIVE = $(SRC_NAME)-src.tar.gz
SRC_URL = https://www.privoxy.org/sf-download-mirror/Sources/4.2.0%20%28stable%29/$(SRC_ARCHIVE)
SRC_SHA256 = 6f91267f81f626c416994db89ab62f4d09246eebf4754b81186e13a18ee9028f

CFLAGS += -ffunction-sections -fdata-sections -fvisibility=hidden
LDFLAGS += -Wl,--gc-sections

.PHONY: all download_test extract_test config_test configure romfs clean
all: config_test
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

download_test:
	test -f $(SRC_ARCHIVE) || wget -t5 --timeout=20 -O $(SRC_ARCHIVE) '$(SRC_URL)'
	echo "$(SRC_SHA256)  $(SRC_ARCHIVE)" | sha256sum -c -

extract_test: download_test
	test -d $(SRC_NAME) || tar xzf $(SRC_ARCHIVE)

config_test: extract_test
	test -f config_done || $(MAKE) configure

configure:
	test -f $(STAGEDIR)/include/pcre2.h
	test -f $(STAGEDIR)/lib/libpcre2-8.so
	test -f $(STAGEDIR)/lib/libpcre2-posix.so
	cd $(SRC_NAME) && autoheader && autoconf && \
		CC="$(CC)" CFLAGS="$(CFLAGS)" \
		CPPFLAGS="-I$(STAGEDIR)/include" \
		LDFLAGS="$(LDFLAGS) -L$(STAGEDIR)/lib -Wl,-rpath-link,$(STAGEDIR)/lib" \
		./configure --prefix=/usr --sysconfdir=/etc/storage/privoxy \
			$(if $(filter y,$(CONFIG_IPV6)),--enable-ipv6-support,--disable-ipv6-support) \
			--disable-pcre-jit-compilation \
			--without-openssl --without-mbedtls --without-wolfssl \
			--host=$(HOST_TARGET) --build=$(HOST_BUILD)
	touch config_done

romfs:
	$(ROMFSINST) $(SRC_NAME)/privoxy /usr/sbin/privoxy
	$(ROMFSINST) -p +x /usr/bin/privoxy.sh
	mkdir -p $(INSTALLDIR)/usr/share/privoxy/templates
	$(ROMFSINST) $(SRC_NAME)/templates /usr/share/privoxy/templates
	mkdir -p configs
	cp -f $(SRC_NAME)/config $(SRC_NAME)/default.filter $(SRC_NAME)/user.filter \
		$(SRC_NAME)/default.action $(SRC_NAME)/match-all.action $(SRC_NAME)/user.action configs/
	cp -f $(SRC_NAME)/trust configs/user.trust
	# Compact only the new ROMFS seed; never rewrite existing user storage files.
	awk '!/^[[:space:]]*#/ && !/^[[:space:]]*$$/' $(SRC_NAME)/config > configs/config
	sed -i 's/^logfile/#logfile/;s|^logdir.*|logdir /tmp|;s|^confdir.*|confdir /etc/storage/privoxy|;s/^#trustfile.*/#trustfile user.trust/;s/^enable-edit-actions.*/enable-edit-actions 1/' configs/config
	printf '\n## Forward to TOR\n#forward-socks5t / 127.0.0.1:9050 .\n#forward-socks5t .onion 127.0.0.1:9050 .\n#forward 192.168.*.*/ .\n#forward 10.*.*.*/ .\n' >> configs/config
	mkdir -p $(INSTALLDIR)/usr/share/privoxy/privoxy
	$(ROMFSINST) configs /usr/share/privoxy/privoxy
	ln -sfn /usr/share/privoxy/templates $(INSTALLDIR)/usr/share/privoxy/privoxy/templates

clean:
	@if [ -f $(SRC_NAME)/GNUmakefile ]; then $(MAKE) -C $(SRC_NAME) distclean; fi
	rm -f config_done
