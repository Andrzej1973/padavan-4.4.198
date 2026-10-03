# Use the userspace that matches the pinned Linux 4.4 USBIP sysfs ABI.
SRC_DIR = $(ROOTDIR)/linux-4.4.x/tools/usb/usbip

.PHONY: all configure romfs clean
all: $(SRC_DIR)/Makefile
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_DIR)

$(SRC_DIR)/configure:
	cd $(SRC_DIR) && autoreconf -fi

$(SRC_DIR)/Makefile: $(SRC_DIR)/configure
	cd $(SRC_DIR) && ./configure \
		--prefix=/usr --disable-shared --enable-static \
		--without-tcp-wrappers --with-usbids-dir=/usr/share \
		--host=$(HOST_TARGET) --build=$(HOST_BUILD)

romfs:
	$(ROMFSINST) -p +x $(SRC_DIR)/src/usbip /sbin/usbip
	$(ROMFSINST) -p +x $(SRC_DIR)/src/usbipd /sbin/usbipd

clean:
	if [ -f $(SRC_DIR)/Makefile ]; then $(MAKE) -C $(SRC_DIR) distclean; fi
