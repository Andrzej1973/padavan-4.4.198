#!/usr/bin/env python3
"""Exercise scheduler audit against actual merged source and commented RTNL include."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("candidate", type=Path)
args = parser.parse_args()
audit = Path(__file__).with_name("audit-aux-family-retry-scheduler.py")
files = ("include/rtmp.h", "common/rtmp_init.c", "ap/ap_apcli_inf.c",
         "os/linux/rt_profile.c", "os/linux/pci_main_dev.c",
         "include/wr-iot-peer-adapter-release.inc",
         "include/wr-iot-aux-family-close-owned.inc", "include/aux-family-retry-scheduler.h")
with tempfile.TemporaryDirectory(prefix="wr-rtnl-regression-") as directory:
    root = Path(directory)
    for name in files:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.candidate / name, target)
    subprocess.run([sys.executable, str(audit), str(root), str(root / "positive.json")], check=True)
    source = root / "ap/ap_apcli_inf.c"
    original = source.read_bytes()
    marker = b"#include <linux/rtnetlink.h>"
    assert original.count(marker) == 1
    for label, replacement in (("commented", b"/* " + marker + b" */"), ("missing", b"")):
        source.write_bytes(original.replace(marker, replacement))
        result = subprocess.run([sys.executable, str(audit), str(root), str(root / (label + ".json"))], capture_output=True, text=True)
        assert result.returncode != 0 and "active_apcli.count" in result.stderr, result.stderr
        assert not (root / (label + ".json")).exists()
print("PASS actual merged scheduler audit accepts active RTNL include and rejects commented/missing include")
