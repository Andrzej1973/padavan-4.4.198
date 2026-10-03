SRC_NAME = yaml-0.2.5
SRC_URL = https://github.com/yaml/libyaml/releases/download/0.2.5/$(SRC_NAME).tar.gz
SRC_SHA256 = c642ae9b75fee120b2d96c712538bd2cf283228d2337df2cf2988e3c02678ef4

.PHONY: all download_test extract_test configure install romfs clean
all: configure
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

download_test:
	test -f $(SRC_NAME).tar.gz || wget -t5 --timeout=20 -O $(SRC_NAME).tar.gz $(SRC_URL)
	echo "$(SRC_SHA256)  $(SRC_NAME).tar.gz" | sha256sum -c -

extract_test: download_test
	test -d $(SRC_NAME) || tar xzf $(SRC_NAME).tar.gz

configure: extract_test
	@if [ ! -f config_done ]; then \
		cd $(SRC_NAME) && \
		CC="$(CC)" AR="$(AR)" RANLIB="$(RANLIB)" \
		CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" \
		./configure --prefix=/ --libdir=/lib --includedir=/include \
			--disable-shared --enable-static \
			--host=$(HOST_TARGET) --build=$(HOST_BUILD) && \
		touch ../config_done; \
	fi

install: all
	$(MAKE) -C $(SRC_NAME) install DESTDIR="$(STAGEDIR)"

# libyaml is linked statically into the resolver candidate.
romfs:

clean:
	@if [ -f $(SRC_NAME)/Makefile ]; then $(MAKE) -C $(SRC_NAME) distclean; fi
	rm -f config_done
