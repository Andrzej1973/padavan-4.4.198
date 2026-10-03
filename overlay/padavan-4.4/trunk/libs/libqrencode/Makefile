# Ported from nilabsent/padavan-ng d2c5846299949c57a4e867284069900b561dd2a4.
# libqrencode 4.1.1: pin the resolved upstream tag commit.
SRC_COMMIT = 715e29fd4cd71b6e452ae0f4e36d917b43122ce8
SRC_NAME = libqrencode-$(SRC_COMMIT)
SRC_ARCHIVE = $(SRC_NAME).tar.gz
SRC_URL = https://github.com/fukuchi/libqrencode/archive/$(SRC_COMMIT).tar.gz

.PHONY: all install romfs clean
all: $(SRC_NAME)/Makefile
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

$(SRC_ARCHIVE):
	curl --fail --location --retry 5 --output $@.tmp $(SRC_URL)
	mv $@.tmp $@

$(SRC_NAME)/configure: $(SRC_ARCHIVE)
	tar -xzf $(SRC_ARCHIVE)
	cd $(SRC_NAME) && ./autogen.sh

$(SRC_NAME)/Makefile: $(SRC_NAME)/configure
	cd $(SRC_NAME) && ./configure \
		--prefix=/ --enable-static --disable-shared --without-png \
		--host=$(HOST_TARGET) --build=$(HOST_BUILD)

install: all
	$(MAKE) -C $(SRC_NAME) install DESTDIR=$(DESTDIR)

romfs:
	$(ROMFSINST) $(DESTDIR)/bin/qrencode /usr/bin/qrencode

clean:
	if [ -f $(SRC_NAME)/Makefile ]; then $(MAKE) -C $(SRC_NAME) distclean; fi
