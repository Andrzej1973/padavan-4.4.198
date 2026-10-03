# libudev dependency for the USBIP tools supplied with Linux 4.4.
SRC_COMMIT = 9e7c4e744b9e7813af9acee64b5e8549ea1fbaa3
SRC_NAME = eudev-$(SRC_COMMIT)
SRC_ARCHIVE = $(SRC_NAME).tar.gz
SRC_URL = https://github.com/eudev-project/eudev/archive/$(SRC_COMMIT).tar.gz

.PHONY: all install romfs clean
all: $(SRC_NAME)/Makefile
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

$(SRC_ARCHIVE):
	curl --fail --location --retry 5 --output $@.tmp $(SRC_URL)
	mv $@.tmp $@

$(SRC_NAME)/configure: $(SRC_ARCHIVE)
	tar -xzf $(SRC_ARCHIVE)
	cd $(SRC_NAME) && autoreconf -fi

$(SRC_NAME)/Makefile: $(SRC_NAME)/configure
	cd $(SRC_NAME) && ./configure \
		--prefix=/ --libdir=/lib --with-rootlibdir=/lib \
		--disable-programs --disable-hwdb --disable-manpages \
		--disable-blkid --disable-selinux --disable-kmod \
		--disable-rule-generator --disable-mtd_probe \
		--enable-shared --disable-static \
		--host=$(HOST_TARGET) --build=$(HOST_BUILD)

install: all
	$(MAKE) -C $(SRC_NAME) install DESTDIR=$(DESTDIR)

romfs:
	$(ROMFSINST) $(DESTDIR)/lib/libudev.so.1.6.3 /lib/libudev.so.1.6.3
	$(ROMFSINST) -s libudev.so.1.6.3 /lib/libudev.so.1

clean:
	if [ -f $(SRC_NAME)/Makefile ]; then $(MAKE) -C $(SRC_NAME) distclean; fi
