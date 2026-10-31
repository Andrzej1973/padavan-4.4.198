#!/usr/bin/env python3
"""Propagate WDS removal refusal through an isolated MT76x3 candidate.

This is only the first release-path repair. It does not prove checked close,
callback quiescence, or safe adapter release and must not be packaged alone.
"""

import argparse
import shutil
from pathlib import Path


def replace_exact(path: Path, old: bytes, new: bytes) -> None:
    data = path.read_bytes()
    if b"\r\n" in data:
        old = old.replace(b"\n", b"\r\n")
        new = new.replace(b"\n", b"\r\n")
    if data.count(old) != 1:
        raise ValueError(f"expected one source anchor in {path}, found {data.count(old)}")
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

    replace_exact(
        root / "ap/ap_wds.c",
        b"VOID WDS_Remove(RTMP_ADAPTER *pAd)",
        b"INT WDS_Remove(RTMP_ADAPTER *pAd)",
    )
    replace_exact(
        root / "include/ap_wds.h",
        b"VOID WDS_Remove(RTMP_ADAPTER *pAd);",
        b"INT WDS_Remove(RTMP_ADAPTER *pAd);",
    )
    replace_exact(
        root / "ap/ap_wds.c",
        b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\tcontinue;",
        b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;",
    )
    replace_exact(
        root / "ap/ap_wds.c",
        b"\t}\n}\n\n\nBOOLEAN WDS_StatsGet",
        b"\t}\n\treturn NDIS_STATUS_SUCCESS;\n}\n\n\nBOOLEAN WDS_StatsGet",
    )
    replace_exact(
        root / "common/cmm_cfg.c",
        b"case CMD_RTPRIV_IOCTL_WDS_REMOVE:\n\t\t\tWDS_Remove(pAd);\n\t\t\tbreak;",
        b"case CMD_RTPRIV_IOCTL_WDS_REMOVE:\n\t\t\tif (WDS_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\tbreak;",
    )
    replace_exact(
        root / "ap/ap_wds_inf.c",
        b"VOID RT28xx_WDS_Remove(VOID *pAd)\n{\n\tRTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_WDS_REMOVE, 0, NULL, 0);\n}",
        b"INT RT28xx_WDS_Remove(VOID *pAd)\n{\n\treturn RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_WDS_REMOVE, 0, NULL, 0);\n}",
    )
    replace_exact(
        root / "include/rt_os_net.h",
        b"VOID RT28xx_WDS_Remove(VOID *pAd);",
        b"INT RT28xx_WDS_Remove(VOID *pAd);",
    )
    replace_exact(
        root / "os/linux/rt_main_dev.c",
        b"\tRT28xx_WDS_Remove(pAd);",
        b"\tif (RT28xx_WDS_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\treturn FALSE;",
    )


if __name__ == "__main__":
    main()
