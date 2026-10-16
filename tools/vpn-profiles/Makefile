WG_SRC = $(ROOTDIR)/user/wireguard-tools/wireguard-tools-1.0.20210914/src
AWG_SRC = $(ROOTDIR)/user/amneziawg/amneziawg-tools-ee0f0a9aa34ff0a0da4b3433b9512781cfe02843/src

PROGRAMS = profilectl validate-wg
ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)
PROGRAMS += validate-awg
endif

.PHONY: all romfs clean
all: $(PROGRAMS)

profilectl: profilectl.c store.c store.h resources.h validate-process.c validate-process.h link-observation.c link-observation.h
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -Wall -Wextra -Werror $(LDFLAGS) -o $@ profilectl.c store.c validate-process.c link-observation.c -lrt

validate-wg: validate-client.c store.h resources.h $(WG_SRC)/config.c $(WG_SRC)/encoding.c
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -I$(WG_SRC) -idirafter $(WG_SRC)/uapi/linux $(LDFLAGS) -o $@ validate-client.c $(WG_SRC)/config.c $(WG_SRC)/encoding.c

validate-awg: validate-client.c store.h resources.h $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/type.c
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -I$(AWG_SRC) -I$(AWG_SRC)/uapi/linux $(LDFLAGS) -o $@ validate-client.c $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/type.c

romfs:
	mkdir -p $(ROMFSDIR)/usr/libexec/wrvpn
	$(ROMFSINST) -p +x profilectl /usr/sbin/wr-vpn-profile
	$(ROMFSINST) -p +x validate-wg /usr/libexec/wrvpn/validate-wg
	$(ROMFSINST) -p +x $(WG_SRC)/wg /usr/libexec/wrvpn/wg
ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)
	$(ROMFSINST) -p +x validate-awg /usr/libexec/wrvpn/validate-awg
	$(ROMFSINST) -p +x $(AWG_SRC)/wg /usr/libexec/wrvpn/awg
endif

clean:
	rm -f profilectl validate-wg validate-awg
