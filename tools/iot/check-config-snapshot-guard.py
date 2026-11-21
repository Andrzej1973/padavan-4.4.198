#!/usr/bin/env python3
"""Verify snapshot source gate using the existing pinned kernel transform."""
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
shared = here.parent / "band-steering"
verify = runpy.run_path(str(here / "config-snapshot-guard.py"))["verify"]
with tempfile.TemporaryDirectory(prefix="wr-config-snapshot-") as directory:
    trunk = Path(directory) / "trunk"
    rc = trunk / "user/rc"
    rc.mkdir(parents=True)
    kernel = trunk / "linux-4.4.x"
    source = kernel / "drivers/nvram/nvram.c"
    source.parent.mkdir(parents=True)
    source.write_bytes((here / "fixtures/config-native-getall.c").read_bytes())
    (kernel / ".config").write_text("# CONFIG_MTD_NAND_MTK is not set\n")
    native_header = kernel / "include/nvram/bcmnvram.h"
    native_header.parent.mkdir(parents=True)
    native_header.write_bytes((here / "fixtures/config-bcmnvram.h").read_bytes())
    (trunk / ".config").write_text("CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y\n")
    (rc / "Makefile").write_text("OBJS += wr-band-settings-snapshot.o\n")
    (rc / "wr-band-settings-snapshot.c").write_bytes((shared / "settings-snapshot.c").read_bytes().replace(
        b'"settings-snapshot.h"', b'"wr-band-settings-snapshot.h"'))
    (rc / "wr-band-settings-snapshot.h").write_bytes((shared / "settings-snapshot.h").read_bytes())

    def refused():
        try:
            verify(trunk, rc)
        except ValueError:
            return
        raise AssertionError("Unsupported snapshot provider was accepted")

    refused()  # Native getall silently truncates before existing transform.
    subprocess.run([sys.executable, str(shared / "prepare-nvram-snapshot.py"),
                    "--kernel-root", str(kernel)], check=True)
    expected = verify(trunk, rc)
    assert expected["verified"] is True
    assert expected["nvram_space"] == 61440 and expected["nvram_header_bytes"] == 20
    kernel_config = kernel / ".config"
    original_config = kernel_config.read_bytes()
    for flags, capacity in [("CONFIG_MTD_NAND_MTK=y\n", 0x20000),
                            ("CONFIG_MTD_NAND_RALINK=y\nCONFIG_MTD_NAND_USE_UBI_PART=y\n", 0x1F000)]:
        kernel_config.write_text(flags)
        assert verify(trunk, rc)["nvram_space"] == capacity
    kernel_config.write_bytes(original_config)
    for path, wrong in [
        (trunk / ".config", "# CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING is not set\n"),
        (rc / "Makefile", "OBJS += unrelated.o\n"),
        (rc / "wr-band-settings-snapshot.c", "bad implementation\n"),
        (rc / "wr-band-settings-snapshot.h", "bad declaration\n"),
        (source, source.read_text().replace("return -ENOSPC;", "break;")),
        (source, source.read_text().replace("return -ENOSPC; /* Preserve live tuples and flash on overflow. */", "break;")),
        (source, source.read_text().replace("#include <linux/errno.h>\n", "")),
        (native_header, native_header.read_text().replace("NVRAM_HEADER_SIZE\t20", "NVRAM_HEADER_SIZE\t24")),
    ]:
        original = path.read_bytes()
        path.write_text(wrong)
        refused()
        path.write_bytes(original)
    header = rc / "wr-band-settings-snapshot.h"
    backup = rc / "snapshot-reference.h"
    header.rename(backup)
    header.symlink_to(backup.name)
    refused()
    header.unlink()
    backup.rename(header)
    assert verify(trunk, rc) == expected
print("PASS native snapshot source gate: pinned ENOSPC transform, selected/linked exact provider; old overflow behavior, changed code/header/config/linkage and symlinks refuse")
