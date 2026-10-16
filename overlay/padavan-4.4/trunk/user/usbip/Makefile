# Use the userspace that matches the pinned Linux 4.4 USBIP sysfs ABI.
SRC_DIR = $(ROOTDIR)/linux-4.4.x/tools/usb/usbip

.PHONY: all configure romfs clean
all: $(SRC_DIR)/Makefile export-table
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_DIR)

export-table: export-table.c export-store.h export-codec.h export-rules.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ export-table.c

$(SRC_DIR)/configure:
	cd $(SRC_DIR) && autoreconf -fi

$(SRC_DIR)/Makefile: $(SRC_DIR)/configure
	cd $(SRC_DIR) && ./configure \
		--prefix=/usr --disable-shared --enable-static \
		--without-tcp-wrappers --with-usbids-dir=/usr/share \
		--host=$(HOST_TARGET) --build=$(HOST_BUILD)

romfs:
	mkdir -p $(ROMFSDIR)/usr/libexec/wr-usbip
	$(ROMFSINST) -p +x $(SRC_DIR)/src/usbip /sbin/usbip
	$(ROMFSINST) -p +x $(SRC_DIR)/src/usbipd /sbin/usbipd
	$(ROMFSINST) -p +x service.sh /usr/sbin/wr-usbip
	$(ROMFSINST) -p +x export-table /usr/libexec/wr-usbip/export-table
	$(ROMFSINST) -p 600 firewall-policy.sh /usr/libexec/wr-usbip/firewall-policy.sh
	$(ROMFSINST) -p 600 device-policy.sh /usr/libexec/wr-usbip/device-policy.sh
	$(ROMFSINST) -p 600 device-action.sh /usr/libexec/wr-usbip/device-action.sh

clean:
	rm -f export-table
	if [ -f $(SRC_DIR)/Makefile ]; then $(MAKE) -C $(SRC_DIR) distclean; fi
