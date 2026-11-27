SRC_NAME = ndisc6-1.0.8
SRC_URL = https://www.remlab.net/files/ndisc6/$(SRC_NAME).tar.bz2
SRC_SHA256 = 1f2fb2dc1172770aa5a09d39738a44d8b753cc5e2e25e306ca78682f9fea0b4f
THISDIR = $(shell pwd)

all: config_test
	$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME)

download_test:
	@set -eu; \
	archive="$(SRC_NAME).tar.bz2"; \
	if [ ! -f "$$archive" ]; then \
		tmp=$$(mktemp "$$archive.XXXXXX"); \
		trap 'rm -f -- "$$tmp"' EXIT; \
		wget -t5 --timeout=20 -O "$$tmp" "$(SRC_URL)"; \
		printf '%s  %s\n' "$(SRC_SHA256)" "$$tmp" | sha256sum -c -; \
		mv -f -- "$$tmp" "$$archive"; \
	else \
		printf '%s  %s\n' "$(SRC_SHA256)" "$$archive" | sha256sum -c -; \
	fi

extract_test: download_test
	( if [ ! -d $(SRC_NAME) ]; then \
		tar xf $(SRC_NAME).tar.bz2; \
	fi )

config_test: extract_test
	( if [ -f ./config_done ]; then \
		echo "the same configuration"; \
	else \
		make configure && touch config_done; \
	fi )

configure:
	( cd $(SRC_NAME) ; \
	rdc_cv_build_hostname=padavan-builder ./configure \
		--prefix=/usr \
		--host=$(HOST_TARGET) \
		--build=$(HOST_BUILD) ; \
	)

clean:
	if [ -f $(SRC_NAME)/Makefile ] ; then \
		$(MAKE) -C $(SRC_NAME) distclean ; \
	fi ; \
	rm -f config_done $(SRC_NAME).tar.bz2

romfs:
	$(ROMFSINST) -p +x $(THISDIR)/$(SRC_NAME)/ndisc6 /usr/bin/ndisc6
	$(ROMFSINST) -p +x $(THISDIR)/$(SRC_NAME)/rdisc6 /usr/bin/rdisc6
