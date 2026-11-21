#!/usr/bin/env python3
"""Move isolated AUX close-phase gate before unregister under RTNL."""

import argparse
import shutil
from pathlib import Path


def replace_exact(path: Path, old: bytes, new: bytes) -> None:
    data = path.read_bytes()
    if b"\r\n" in data:
        old = old.replace(b"\n", b"\r\n")
        new = new.replace(b"\n", b"\r\n")
    if data.count(old) != 1:
        raise ValueError(f"expected one anchor in {path}, found {data.count(old)}")
    path.write_bytes(data.replace(old, new, 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.source.is_dir() or args.output.exists():
        raise ValueError("source must exist and output must not exist")
    shutil.copytree(args.source, args.output)
    root = args.output
    for relative, indent in (
        ("ap/ap_wds.c", b"\t\t\t"),
        ("ap/ap_apcli.c", b"\t\t\t"),
        ("sniffer/sniffer_radiotap.c", b"\t\t"),
    ):
        path = root / relative
        old = (
            indent + b"RtmpOSNetDevProtect(1);\n"
            + indent + b"RtmpOSNetDevDetach(wdev->if_dev);\n"
            + indent + b"RtmpOSNetDevProtect(0);\n"
            + indent + b"if (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n"
            + indent + b"\treturn NDIS_STATUS_FAILURE;"
        )
        new = (
            indent + b"RtmpOSNetDevProtect(1);\n"
            + indent + b"RtmpOSNetDevClose(wdev->if_dev);\n"
            + indent + b"if (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS) {\n"
            + indent + b"\tRtmpOSNetDevProtect(0);\n"
            + indent + b"\treturn NDIS_STATUS_FAILURE;\n"
            + indent + b"}\n"
            + indent + b"RtmpOSNetDevDetach(wdev->if_dev);\n"
            + indent + b"RtmpOSNetDevProtect(0);"
        )
        replace_exact(path, old, new)
    replace_exact(
        root / "include/wr-iot-netdev-registration.inc",
        b"/* Unregister invokes ndo_stop but does not propagate its driver result.\n * Keep the netdev allocated unless the owned reference was consumed. */",
        b"/* dev_close under RTNL does not propagate ndo_stop's driver result.\n * Verify consumed reference before unregister frees netdev_ops. */",
    )


if __name__ == "__main__":
    main()
