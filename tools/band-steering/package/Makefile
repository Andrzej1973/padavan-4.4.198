# Candidate package only; no active user/Makefile registration or autostart.
SOURCE_DIR ?= ..
BUILD_DIR ?= build
LAYOUT_DIR ?= .
INSTALLDIR ?= romfs
CC ?= cc
CFLAGS ?= -O2
CPPFLAGS += -I$(SOURCE_DIR) -I$(LAYOUT_DIR)
WARNINGS = -std=c11 -Wall -Wextra -Werror
DAEMON_SOURCES = protocol session clients aging policy grants coordinator loop \
                 events framing listener transport control main
DAEMON_FILES = $(addprefix $(SOURCE_DIR)/,$(addsuffix .c,$(DAEMON_SOURCES)))
HEADERS = $(wildcard $(SOURCE_DIR)/*.h)
.PHONY: all romfs clean
all: $(BUILD_DIR)/wr-band-steering $(BUILD_DIR)/wr-band-steering-ctl
$(BUILD_DIR):
	mkdir -p "$@"
$(BUILD_DIR)/wr-band-steering: $(DAEMON_FILES) $(HEADERS) $(LAYOUT_DIR)/protocol-layout.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(WARNINGS) $(DAEMON_FILES) $(LDFLAGS) -lrt $(LDLIBS) -o "$@"
$(BUILD_DIR)/wr-band-steering-ctl: $(SOURCE_DIR)/ctl.c $(SOURCE_DIR)/control-client.c $(SOURCE_DIR)/control-client.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(WARNINGS) $(SOURCE_DIR)/ctl.c $(SOURCE_DIR)/control-client.c $(LDFLAGS) $(LDLIBS) -o "$@"
romfs: all
	install -d "$(INSTALLDIR)/usr/sbin"
	install -m 0755 "$(BUILD_DIR)/wr-band-steering" "$(INSTALLDIR)/usr/sbin/wr-band-steering"
	install -m 0755 "$(BUILD_DIR)/wr-band-steering-ctl" "$(INSTALLDIR)/usr/sbin/wr-band-steering-ctl"
clean:
	rm -f "$(BUILD_DIR)/wr-band-steering" "$(BUILD_DIR)/wr-band-steering-ctl"
