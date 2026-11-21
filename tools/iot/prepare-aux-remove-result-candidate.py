#!/usr/bin/env python3
"""Stage AP-client and monitor checked removal results after WDS v35.

The output is an isolated driver candidate, not a production integration.
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

    replace_exact(root / "ap/ap_apcli.c", b"VOID ApCli_Remove(RTMP_ADAPTER *pAd)", b"INT ApCli_Remove(RTMP_ADAPTER *pAd)")
    replace_exact(root / "include/ap_apcli.h", b"VOID ApCli_Remove(", b"INT ApCli_Remove(")
    replace_exact(root / "ap/ap_apcli.c", b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\tcontinue;", b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;")
    replace_exact(root / "ap/ap_apcli.c", b"\t}\n}\n\n\nBOOLEAN ApCli_Open", b"\t}\n\treturn NDIS_STATUS_SUCCESS;\n}\n\n\nBOOLEAN ApCli_Open")
    replace_exact(root / "ap/ap_cfg.c", b"case CMD_RTPRIV_IOCTL_APC_REMOVE:\n\t\t\tApCli_Remove(pAd);\n\t\t\tbreak;", b"case CMD_RTPRIV_IOCTL_APC_REMOVE:\n\t\t\tif (ApCli_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\tbreak;")
    replace_exact(root / "ap/ap_apcli_inf.c", b"VOID RT28xx_ApCli_Remove(VOID *pAd)", b"INT RT28xx_ApCli_Remove(VOID *pAd)")
    replace_exact(root / "ap/ap_apcli_inf.c", b"\tRTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_REMOVE, 0, NULL, 0);", b"\treturn RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_REMOVE, 0, NULL, 0);")

    replace_exact(root / "sniffer/sniffer_radiotap.c", b"VOID Monitor_Remove(RTMP_ADAPTER *pAd)", b"INT Monitor_Remove(RTMP_ADAPTER *pAd)")
    replace_exact(root / "sniffer/sniffer_radiotap.c", b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\treturn;", b"if (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\treturn NDIS_STATUS_FAILURE;")
    replace_exact(root / "sniffer/sniffer_radiotap.c", b"\t}\n\t\n}\nBOOLEAN Monitor_Open", b"\t}\n\treturn NDIS_STATUS_SUCCESS;\n}\nBOOLEAN Monitor_Open")
    replace_exact(root / "include/rtmp.h", b"VOID Monitor_Remove(RTMP_ADAPTER *pAd);", b"INT Monitor_Remove(RTMP_ADAPTER *pAd);")
    replace_exact(root / "common/cmm_cfg.c", b"case CMD_RTPRIV_IOCTL_SNIFF_REMOVE:\n\t\t\tMonitor_Remove(pAd);\n\t\t\tbreak;", b"case CMD_RTPRIV_IOCTL_SNIFF_REMOVE:\n\t\t\tif (Monitor_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\tbreak;")
    replace_exact(root / "os/linux/rt_profile.c", b"VOID RT28xx_Monitor_Remove(VOID *pAd)", b"INT RT28xx_Monitor_Remove(VOID *pAd)")
    replace_exact(root / "os/linux/rt_profile.c", b"\tRTMP_COM_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_SNIFF_REMOVE, 0, NULL, 0);", b"\treturn RTMP_COM_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_SNIFF_REMOVE, 0, NULL, 0);")

    header = root / "include/rt_os_net.h"
    for name in (b"Monitor", b"ApCli"):
        replace_exact(header, b"VOID RT28xx_" + name + b"_Remove(VOID *pAd);", b"INT RT28xx_" + name + b"_Remove(VOID *pAd);")
    main_dev = root / "os/linux/rt_main_dev.c"
    for name in (b"Monitor", b"ApCli"):
        replace_exact(main_dev, b"\tRT28xx_" + name + b"_Remove(pAd);", b"\tif (RT28xx_" + name + b"_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\treturn FALSE;")


if __name__ == "__main__":
    main()
