# Preserve the AmneziaWG tools version used by the original firmware.
SRC_COMMIT = ee0f0a9aa34ff0a0da4b3433b9512781cfe02843
SRC_NAME = amneziawg-tools-$(SRC_COMMIT)
SRC_ARCHIVE = $(SRC_NAME).tar.gz
SRC_URL = https://github.com/amnezia-vpn/amneziawg-tools/archive/$(SRC_COMMIT).tar.gz

.PHONY: all romfs clean
all: $(SRC_NAME)/src/Makefile
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)/src WITH_BASHCOMPLETION=no WITH_WGQUICK=no WITH_SYSTEMDUNITS=no wg

$(SRC_ARCHIVE):
	curl --fail --location --retry 5 --output $@.tmp $(SRC_URL)
	mv $@.tmp $@

$(SRC_NAME)/src/Makefile: $(SRC_ARCHIVE)
	tar -xzf $(SRC_ARCHIVE)

romfs:
	$(ROMFSINST) -p +x $(SRC_NAME)/src/wg /usr/bin/awg
	$(ROMFSINST) -s awg /usr/bin/wg
	$(ROMFSINST) -s ../bin/awg /usr/sbin/wg

clean:
	if [ -f $(SRC_NAME)/src/Makefile ]; then $(MAKE) -C $(SRC_NAME)/src clean; fi
