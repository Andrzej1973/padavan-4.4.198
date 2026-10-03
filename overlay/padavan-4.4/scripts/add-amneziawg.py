#!/usr/bin/env python3
"""Integrate the pinned AmneziaWG module and userspace build hooks."""
from pathlib import Path
import shutil
import sys

target = Path(sys.argv[1]) / "trunk"
source = Path(sys.argv[2]) / "trunk/linux-3.4.x/net/amneziawg"
overlay = Path(__file__).resolve().parent.parent
destination = target / "linux-4.4.x/net/amneziawg"
if destination.exists():
    raise SystemExit("AmneziaWG destination already exists")
shutil.copytree(source, destination)
shutil.copyfile(overlay / "trunk/linux-4.4.x/net/amneziawg/compat/compat.h",
                destination / "compat/compat.h")
shutil.copyfile(overlay / "trunk/linux-4.4.x/net/amneziawg/Kconfig",
                destination / "Kconfig")
chacha_dir = destination / "compat/crypto/chacha/include/crypto"
chacha_dir.mkdir(parents=True)
shutil.copyfile(overlay / "trunk/linux-4.4.x/net/amneziawg/compat/crypto/chacha/include/crypto/chacha.h",
                chacha_dir / "chacha.h")
kbuild = destination / "compat/Kbuild.include"
kbuild.write_text(kbuild.read_text() +
    '\nifeq ($(wildcard $(srctree)/include/crypto/chacha.h),)\n'
    'ccflags-y += -I$(kbuild-dir)/compat/crypto/chacha/include\nendif\n')


def append_once(path, marker, addition):
    text = path.read_text()
    if marker in text:
        raise SystemExit("Unexpected existing hook: " + marker)
    path.write_text(text.rstrip() + "\n" + addition + "\n")

append_once(target / "linux-4.4.x/net/Makefile", "CONFIG_AMNEZIAWG",
            "obj-$(CONFIG_AMNEZIAWG) += amneziawg/")
append_once(target / "linux-4.4.x/net/Kconfig", 'net/amneziawg/Kconfig',
            'source "net/amneziawg/Kconfig"')
user_makefile = target / "user/Makefile"
text = user_makefile.read_text()
anchor = "all: $(patsubst %,%_only,$(dir_y))"
if "CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG" in text or text.count(anchor) != 1:
    raise SystemExit("Unexpected userspace Makefile")
user_makefile.write_text(text.replace(anchor,
    "dir_$(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG) += amneziawg\n\n" + anchor))
append_once(target / "configs/templates/WR1200JS.config",
            "CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG",
            "CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG=n")
(target / "user/amneziawg").mkdir()
shutil.copyfile(overlay / "trunk/user/amneziawg/Makefile",
                target / "user/amneziawg/Makefile")
print("AmneziaWG kernel and userspace build hooks installed")
