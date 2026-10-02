from pathlib import Path
import sys
root = Path(sys.argv[1]) / "trunk"
path = root / "user/Makefile"
text = path.read_text()
start = "ifeq ($(STORAGE_ENABLED),y)\nifeq ($(CONFIG_FIRMWARE_ENABLE_EXT2),y)"
end = "ifeq ($(CONFIG_FIRMWARE_INCLUDE_NTFS_3G),y)\nFS_NTFS_ENABLED=y"
if text.count(start) != 1 or text.count(end) != 1:
    raise SystemExit("Pinned filesystem selection anchors changed")
text = text.replace(start, "ifeq ($(STORAGE_ENABLED),y)\nifeq ($(CONFIG_FIRMWARE_INCLUDE_FS_TOOLS),y)\nifeq ($(CONFIG_FIRMWARE_ENABLE_EXT2),y)")
text = text.replace(end, "endif # CONFIG_FIRMWARE_INCLUDE_FS_TOOLS\n" + end)
path.write_text(text)
path = root / "configs/templates/WR1200JS.config"
text = path.read_text()
if "CONFIG_FIRMWARE_INCLUDE_FS_TOOLS=" in text:
    raise SystemExit("Filesystem tools selector already exists")
path.write_text(text.rstrip() + "\n\n### Include filesystem checking/formatting tools; NTFS driver is separate.\nCONFIG_FIRMWARE_INCLUDE_FS_TOOLS=n\n")
print("Filesystem tools selector restored; NTFS dependency preserved")
