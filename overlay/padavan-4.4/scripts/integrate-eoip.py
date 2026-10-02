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
for name in ("eoipcr.c", "libnetlink.c", "libnetlink.h", "eoip_version.h"):
    shutil.copyfile(assets / name, package / name)
(package / "unified").mkdir(exist_ok=True)
shutil.copyfile(assets / "unified/eoip_proto.h", package / "unified/eoip_proto.h")
(package / "Makefile").write_text("""CFLAGS += -Os -std=gnu99 -ffunction-sections -fdata-sections -fno-strict-aliasing
LDFLAGS += -Wl,--gc-sections
all: eoip-ctl
eoip-ctl: eoipcr.o libnetlink.o
	$(CC) $(LDFLAGS) -o $@ $^
clean:
	rm -f eoip-ctl eoipcr.o libnetlink.o
romfs:
	$(ROMFSINST) eoip-ctl /usr/bin/eoip-ctl
""")
path = root / "user/Makefile"
text = path.read_text()
anchor = "all: $(patsubst %,%_only,$(dir_y))"
if text.count(anchor) != 1:
    raise SystemExit("User package list anchor changed")
path.write_text(text.replace(anchor, "dir_$(CONFIG_FIRMWARE_INCLUDE_EOIP) += eoip-ctl\n\n" + anchor))
print("EoIP IPv4 module and legacy CLI packaging integrated")
