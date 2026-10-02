from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1]) / "trunk"
donor = Path(sys.argv[2]) / "trunk/user/dnsmasq"
package = root / "user/dnsmasq"
required = ("001-regex-server.patch", "002-regex-ipset.patch", "firmware-specific.patch")
for name in required:
    if not (donor / "patches" / name).is_file():
        raise SystemExit("Missing pinned dnsmasq patch: " + name)
if not (donor / "dnsmasq-2.93.tar.xz").is_file():
    raise SystemExit("Pinned dnsmasq archive missing")
for path in (package / "patches").glob("*.patch"):
    path.unlink()
for path in sorted((donor / "patches").glob("*.patch")):
    shutil.copyfile(path, package / "patches" / path.name)
shutil.copyfile(donor / "dnsmasq-2.93.tar.xz", package / "dnsmasq-2.93.tar.xz")
text = (donor / "Makefile").read_text()
text = text.replace("$(if $(CONFIG_FIRMWARE_ENABLE_DNSMASQ_REGEX),", "$(if $(filter y,$(CONFIG_FIRMWARE_ENABLE_DNSMASQ_REGEX)),")
text = text.replace("$(if $(CONFIG_FIRMWARE_INCLUDE_IPSET),", "$(if $(filter y,$(CONFIG_FIRMWARE_INCLUDE_IPSET)),")
anchor = '\t$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME) COPTS='
if text.count(anchor) != 1:
    raise SystemExit("dnsmasq build anchor changed")
text = text.replace(anchor, '\tPKG_CONFIG_PATH= PKG_CONFIG_LIBDIR="$(STAGEDIR)/lib/pkgconfig:$(STAGEDIR)/share/pkgconfig" PKG_CONFIG_SYSROOT_DIR="$(STAGEDIR)" ' + anchor.lstrip())
# Apply each patch with failure propagation rather than a concatenated shell pipeline.
old = "\t\tcat patches/*.patch | patch -d $(SRC_NAME) -r - -N -p1;"
new = "\t\tset -e; for patch_file in patches/*.patch; do patch --batch -d $(SRC_NAME) -p1 -i ../$$patch_file; done;"
if old not in text:
    raise SystemExit("dnsmasq patch anchor changed")
text = text.replace(old, new)
(package / "Makefile").write_text(text)
path = root / "libs/Makefile"
text = path.read_text()
anchor = "LIBS_INCLUDE_LIBPCRE=n"
if text.count(anchor) != 1:
    raise SystemExit("libpcre selector anchor changed")
block = """LIBS_INCLUDE_LIBPCRE=n
ifeq ($(CONFIG_FIRMWARE_ENABLE_DNSMASQ_REGEX),y)
LIBS_INCLUDE_LIBPCRE=y
endif"""
path.write_text(text.replace(anchor, block))
path = root / "configs/templates/WR1200JS.config"
text = path.read_text()
if "CONFIG_FIRMWARE_ENABLE_DNSMASQ_REGEX=" in text:
    raise SystemExit("Regex selector already exists")
path.write_text(text.rstrip() + "\nCONFIG_FIRMWARE_ENABLE_DNSMASQ_REGEX=n\n")
print("Pinned dnsmasq 2.93 and regex/IPSet patches integrated")
