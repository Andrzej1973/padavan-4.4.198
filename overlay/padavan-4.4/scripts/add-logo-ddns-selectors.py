from pathlib import Path
import shutil
import sys
root = Path(sys.argv[1]) / "trunk"
donor = Path(sys.argv[2]) / "trunk"
config = root / "configs/templates/WR1200JS.config"
text = config.read_text()
for key in ("CONFIG_FIRMWARE_INCLUDE_VENDOR_LOGO", "CONFIG_FIRMWARE_INCLUDE_DDNS_SSL"):
    if key + "=" in text:
        raise SystemExit("Selector already exists: " + key)
    text += "\n" + key + "=n\n"
config.write_text(text)
logo = root / "user/www/logo"
logo.mkdir(exist_ok=True)
shutil.copyfile(donor / "user/www/logo/padavan.png", logo / "padavan.png")
path = root / "user/www/Makefile"
text = path.read_text()
anchor = "\tcp -R $(WEBUI_NAME) $(ROMFS_DIR)/www"
if text.count(anchor) != 1:
    raise SystemExit("WebUI copy anchor changed")
block = """
ifeq ($(CONFIG_FIRMWARE_INCLUDE_VENDOR_LOGO),y)
	# YOUHUA had no dedicated asset in the pinned source; preserve Padavan fallback.
	cp -f logo/padavan.png $(ROMFS_DIR)/www/bootstrap/img/logo.png
endif"""
path.write_text(text.replace(anchor, anchor + block))
path = root / "user/inadyn/Makefile"
text = path.read_text()
if text.count("--enable-openssl") != 1:
    raise SystemExit("inadyn TLS configure anchor changed")
text = text.replace("--enable-openssl", "$(if $(filter y,$(CONFIG_FIRMWARE_INCLUDE_DDNS_SSL)),--enable-openssl,--disable-ssl)")
path.write_text(text)
print("Vendor logo fallback and DDNS TLS selectors integrated")
