WG_SRC = $(ROOTDIR)/user/wireguard-tools/wireguard-tools-1.0.20210914/src
AWG_SRC = $(ROOTDIR)/user/amneziawg/amneziawg-tools-ee0f0a9aa34ff0a0da4b3433b9512781cfe02843/src

PROGRAMS = profilectl validate-wg readback-wg
ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)
PROGRAMS += validate-awg readback-awg
endif

.PHONY: all romfs clean
all: $(PROGRAMS)

profilectl: profilectl.c protect.h endpoint-pin.c endpoint-pin.h store.c store.h resources.h validate-process.c validate-process.h link-observation.c link-observation.h runtime-state.c runtime-state.h config-transaction.c config-transaction.h config-apply.c config-apply.h config-plan.c config-plan.h plan-report.c plan-report.h addr-apply.c addr-apply.h route-apply.c route-apply.h profile-apply.c profile-apply.h dns-apply.c dns-apply.h link-actions.c link-actions.h link-lifecycle.c link-lifecycle.h
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -Wall -Wextra -Werror $(LDFLAGS) -o $@ profilectl.c store.c validate-process.c link-observation.c runtime-state.c config-transaction.c config-apply.c config-plan.c plan-report.c addr-apply.c route-apply.c profile-apply.c dns-apply.c link-actions.c link-lifecycle.c endpoint-pin.c -lrt

validate-wg: validate-client.c store.h resources.h $(WG_SRC)/config.c $(WG_SRC)/encoding.c
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -I$(WG_SRC) -idirafter $(WG_SRC)/uapi/linux $(LDFLAGS) -o $@ validate-client.c $(WG_SRC)/config.c $(WG_SRC)/encoding.c

validate-awg: validate-client.c store.h resources.h $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/type.c
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -I$(AWG_SRC) -I$(AWG_SRC)/uapi/linux $(LDFLAGS) -o $@ validate-client.c $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/type.c

readback-wg: config-readback.c resources.h $(WG_SRC)/config.c $(WG_SRC)/encoding.c $(WG_SRC)/ipc.c $(WG_SRC)/curve25519.c $(wildcard $(WG_SRC)/*.h)
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -DRUNSTATEDIR='"/var/run"' -I$(WG_SRC) -idirafter $(WG_SRC)/uapi/linux $(LDFLAGS) -o $@ config-readback.c $(WG_SRC)/config.c $(WG_SRC)/encoding.c $(WG_SRC)/ipc.c $(WG_SRC)/curve25519.c -Wl,--wrap=getaddrinfo

readback-awg: config-readback.c resources.h $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/ipc.c $(AWG_SRC)/curve25519.c $(AWG_SRC)/type.c $(wildcard $(AWG_SRC)/*.h)
	$(CC) $(CFLAGS) -std=gnu99 -D_GNU_SOURCE -DWR_VPN_NATIVE_AWG -DRUNSTATEDIR='"/var/run"' -I$(AWG_SRC) -I$(AWG_SRC)/uapi/linux $(LDFLAGS) -o $@ config-readback.c $(AWG_SRC)/config.c $(AWG_SRC)/encoding.c $(AWG_SRC)/ipc.c $(AWG_SRC)/curve25519.c $(AWG_SRC)/type.c -Wl,--wrap=getaddrinfo

romfs:
	mkdir -p $(ROMFSDIR)/usr/libexec/wrvpn
	$(ROMFSINST) -p +x profilectl /usr/sbin/wr-vpn-profile
	$(ROMFSINST) -p +x service.sh /usr/sbin/wr-vpn-profiles-service
	$(ROMFSINST) -p +x validate-wg /usr/libexec/wrvpn/validate-wg
	$(ROMFSINST) -p +x readback-wg /usr/libexec/wrvpn/readback-wg
	$(ROMFSINST) -p +x $(WG_SRC)/wg /usr/libexec/wrvpn/wg
ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)
	$(ROMFSINST) -p +x validate-awg /usr/libexec/wrvpn/validate-awg
	$(ROMFSINST) -p +x readback-awg /usr/libexec/wrvpn/readback-awg
	$(ROMFSINST) -p +x $(AWG_SRC)/wg /usr/libexec/wrvpn/awg
endif

clean:
	rm -f profilectl validate-wg validate-awg readback-wg readback-awg
