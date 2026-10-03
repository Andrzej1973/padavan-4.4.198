from pathlib import Path
import sys

root = Path(sys.argv[1]) / "trunk"
makefile = root / "user/Makefile"
text = makefile.read_text()
old = "dir_$(CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS)\t+= lua51"
new = """# Lua is a user-selectable package and a Shadowsocks dependency.
ifneq (,$(filter y,$(CONFIG_FIRMWARE_INCLUDE_LUA) $(CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS)))
dir_y += lua51
endif"""
if text.count(old) != 1:
    raise SystemExit("Pinned Lua dependency anchor changed")
if not (root / "user/lua51/Makefile").is_file():
    raise SystemExit("Native Lua recipe missing")
makefile.write_text(text.replace(old, new))
config = root / "configs/templates/WR1200JS.config"
text = config.read_text()
if "CONFIG_FIRMWARE_INCLUDE_LUA=" in text:
    raise SystemExit("Lua selector already exists; inspect before applying")
config.write_text(text.rstrip() + "\n\n### Include Lua 5.1 runtime (also required by Shadowsocks).\nCONFIG_FIRMWARE_INCLUDE_LUA=n\n")
print("Native Lua package selector added; Shadowsocks dependency preserved")
