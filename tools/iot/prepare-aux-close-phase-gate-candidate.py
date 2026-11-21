#!/usr/bin/env python3
"""Stage a post-unregister close-phase gate in an isolated MT76x3 tree.

This does not establish callback quiescence or safe PCI adapter release.
"""

import argparse
import shutil
from pathlib import Path


GATE = b'''/* Unregister invokes ndo_stop but does not propagate its driver result.
 * Keep the netdev allocated unless the owned reference was consumed. */
INT wr_iot_netdev_close_phase_idle(RTMP_ADAPTER *pAd, PNET_DEV dev)
{
 struct wr_iot_interface_ref *record=NULL;
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++)
  if(pAd->wr_iot_interface_refs[i].device==dev){
   record=&pAd->wr_iot_interface_refs[i];break;
  }
 if(record&&record->published&&record->removing&&
    record->phase==WR_REF_IDLE&&!pAd->wr_iot_registration_inflight)
  status=NDIS_STATUS_SUCCESS;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}

'''


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
    replace_exact(
        root / "include/wr-iot-netdev-registration.inc",
        b"/* Use only when the attempted removal made no vendor/kernel mutation.",
        GATE + b"/* Use only when the attempted removal made no vendor/kernel mutation.",
    )
    replace_exact(
        root / "include/rtmp.h",
        b"INT wr_iot_netdev_mark_removing(RTMP_ADAPTER *pAd, PNET_DEV dev);",
        b"INT wr_iot_netdev_mark_removing(RTMP_ADAPTER *pAd, PNET_DEV dev);\nINT wr_iot_netdev_close_phase_idle(RTMP_ADAPTER *pAd, PNET_DEV dev);",
    )
    for relative in ("ap/ap_wds.c", "ap/ap_apcli.c", "sniffer/sniffer_radiotap.c"):
        path = root / relative
        replace_exact(
            path,
            b"RtmpOSNetDevProtect(0);\n\n\t\t\trtmp_wdev_idx_unreg(pAd, wdev);" if relative != "sniffer/sniffer_radiotap.c" else b"RtmpOSNetDevProtect(0);\n\t\trtmp_wdev_idx_unreg(pAd, wdev);",
            b"RtmpOSNetDevProtect(0);\n\t\t\tif (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\n\t\t\trtmp_wdev_idx_unreg(pAd, wdev);" if relative != "sniffer/sniffer_radiotap.c" else b"RtmpOSNetDevProtect(0);\n\t\tif (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\treturn NDIS_STATUS_FAILURE;\n\t\trtmp_wdev_idx_unreg(pAd, wdev);",
        )


if __name__ == "__main__":
    main()
