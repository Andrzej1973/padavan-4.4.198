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
    source = root / "common/rtmp_init.c"
    original = source.read_bytes()
    marker = b"#include <linux/rtnetlink.h>"
    assert original.count(marker) == 1
    for label, replacement in (("commented", b"/* " + marker + b" */"), ("missing", b"")):
        source.write_bytes(original.replace(marker, replacement))
        result = subprocess.run([sys.executable, str(audit), str(root), str(root / (label + ".json"))], capture_output=True, text=True)
        assert result.returncode != 0 and "active_init.count" in result.stderr, result.stderr
        assert not (root / (label + ".json")).exists()
    source.write_bytes(original)
    pci = root / "os/linux/pci_main_dev.c"
    pci_original = pci.read_text()
    start = pci_original.index("static VOID DEVEXIT rt_pci_remove(")
    prefix, removal = pci_original[:start], pci_original[start:]
    call = "RtmpRaDevCtrlExit(pAd)"
    join = "cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);"
    assert removal.count(call) == 1 and removal.count(join) == 2
    # Move the release call before the first external join. Counts remain
    # unchanged, so only the path-order check must reject this regression.
    removal = removal.replace(call, "wr_test_release_placeholder(pAd)")
    removal = removal.replace(join, call + ";" + join, 1)
    pci.write_text(prefix + removal)
    result = subprocess.run([sys.executable, str(audit), str(root), str(root / "early-release.json")], capture_output=True, text=True)
    assert result.returncode != 0 and "first_flush<retire" in result.stderr, result.stderr
    assert not (root / "early-release.json").exists()
print("PASS actual merged scheduler audit accepts active RTNL include and rejects commented/missing include")
print("PASS scheduler removal audit rejects adapter release before worker join")
