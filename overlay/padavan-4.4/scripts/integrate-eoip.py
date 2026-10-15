from pathlib import Path
import shutil
import sys
root = Path(sys.argv[1]) / "trunk"
assets = Path(__file__).resolve().parent.parent / "candidates/eoip"
kernel = root / "linux-4.4.x"
for name in ("eoip.c", "eoip_proto.h", "eoip_keepalive.h"):
    shutil.copyfile(assets / "unified" / name, kernel / "net/ipv4" / name)
shutil.copyfile(assets / "eoip_version.h", kernel / "net/eoip_version.h")
path = kernel / "net/ipv4/Makefile"
text = path.read_text()
if "CONFIG_NET_EOIP)" in text:
    raise SystemExit("EoIP build rule already exists")
path.write_text(text.rstrip() + "\nobj-$(CONFIG_NET_EOIP) += eoip.o\n")
path = kernel / "net/ipv4/Kconfig"
path.write_text(path.read_text().rstrip() + """
config NET_EOIP
	tristate "MikroTik compatible EoIP IPv4 tunnel"
	depends on INET && NETFILTER
	help
	  Standalone EoIP module. No tunnel is created by default.
""")
path = root / "configs/templates/WR1200JS.config"
text = path.read_text()
if "CONFIG_FIRMWARE_INCLUDE_EOIP=" in text:
    raise SystemExit("EoIP selector already exists")
path.write_text(text.rstrip() + "\nCONFIG_FIRMWARE_INCLUDE_EOIP=n\n")
requested = Path("configs.build/wr1200js.config").read_text().splitlines()
path = root / "configs/boards/WR1200JS/kernel-4.4.x.config"
text = path.read_text()
if "CONFIG_NET_EOIP=" in text:
    raise SystemExit("EoIP kernel config already exists")
text += "\n" + ("CONFIG_NET_EOIP=m" if "CONFIG_FIRMWARE_INCLUDE_EOIP=y" in requested else "# CONFIG_NET_EOIP is not set") + "\n"
path.write_text(text)
package = root / "user/eoip-ctl"
package.mkdir(exist_ok=True)
helpers = Path(__file__).resolve().parents[3] / "tools/eoip"
shutil.copyfile(helpers / "boot.sh", package / "wr-eoip-boot")
(package / "wr-eoip-boot").chmod(0o755)
for name in ("observation.h", "netlink-query.h", "config.h", "configure.h",
             "runtime-state.h", "lifecycle.h", "controller.h", "table.h", "worker.c", "stored.h", "nvram-entry.c"):
    shutil.copyfile(helpers / name, package / name)
for name in ("eoipcr.c", "libnetlink.c", "libnetlink.h", "eoip_version.h"):
    shutil.copyfile(assets / name, package / name)
(package / "unified").mkdir(exist_ok=True)
shutil.copyfile(assets / "unified/eoip_proto.h", package / "unified/eoip_proto.h")
(package / "Makefile").write_text("""CFLAGS += -Os -std=gnu99 -ffunction-sections -fdata-sections -fno-strict-aliasing -I../shared
LDFLAGS += -Wl,--gc-sections
all: eoip-ctl eoip-service
eoip-ctl: eoipcr.o libnetlink.o
	$(CC) $(LDFLAGS) -o $@ $^
eoip-service: nvram-entry.o
	$(CC) $(LDFLAGS) -o $@ $^ -L../shared -lshared
nvram-entry.o: nvram-entry.c stored.h worker.c controller.h configure.h lifecycle.h runtime-state.h config.h observation.h netlink-query.h table.h
eoipcr.o: netlink-query.h observation.h
clean:
	rm -f eoip-ctl eoip-service eoipcr.o libnetlink.o nvram-entry.o
romfs:
	$(ROMFSINST) eoip-ctl /usr/bin/eoip-ctl
	$(ROMFSINST) eoip-service /usr/bin/eoip-service
	$(ROMFSINST) wr-eoip-boot /usr/bin/wr-eoip-boot
""")
path = root / "user/Makefile"
text = path.read_text()
anchor = "all: $(patsubst %,%_only,$(dir_y))"
if text.count(anchor) != 1:
    raise SystemExit("User package list anchor changed")
path.write_text(text.replace(anchor, "dir_$(CONFIG_FIRMWARE_INCLUDE_EOIP) += eoip-ctl\n\n" + anchor))
print("EoIP IPv4 module, legacy CLI and managed-service worker packaging integrated")
