#!/usr/bin/env python3
"""Prepare isolated MT76x3 caller-netdev ABI candidate; never install it."""

import argparse
import shutil
from pathlib import Path


CALLERS = {
    "ap/ap_mbss_inf.c": "pDev",
    "ap/ap_apcli_inf.c": "dev_p",
    "ap/ap_wds_inf.c": "dev",
    "os/linux/rt_main_dev.c": "net_dev",
    "os/linux/rt_profile.c": "dev_p",
}


def replace_exact(path: Path, old: bytes, new: bytes, expected: int) -> None:
    content = path.read_bytes()
    count = content.count(old)
    if count != expected:
        raise ValueError(f"{path}: expected {expected} anchors, found {count}")
    path.write_bytes(content.replace(old, new))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not (source / "include/rt_os_net.h").is_file():
        parser.error("source is not a staged MT76x3 driver tree")
    if output.exists() or output == source or source in output.parents or output in source.parents:
        parser.error("output must be a new sibling directory, separate from source")
    for rel, dev in CALLERS.items():
        data = (source / rel).read_bytes()
        for kind in ("UP", "DOWN"):
            if data.count(f"VIRTUAL_IF_{kind}(pAd)".encode()) != 1:
                parser.error(f"unexpected {kind} caller count in {rel}")
        if dev.encode() not in data:
            parser.error(f"netdev variable {dev} absent from {rel}")
    header = (source / "include/rt_os_net.h").read_bytes()
    request = (source / "include/rtmp_cmd.h").read_bytes()
    if header.count(b"RT_CMD_INF_UP_DOWN InfConf = { rt28xx_open, rt28xx_close };") != 2:
        parser.error("unexpected private request initializer")
    if request.count(b"int (*rt28xx_close)(VOID *net_dev);") != 1:
        parser.error("unexpected request ABI")

    shutil.copytree(source, output)
    for rel, dev in CALLERS.items():
        path = output / rel
        for kind in ("UP", "DOWN"):
            replace_exact(path, f"VIRTUAL_IF_{kind}(pAd)".encode(),
                          f"VIRTUAL_IF_{kind}(pAd, {dev})".encode(), 1)
    replace_exact(output / "include/rtmp_cmd.h",
                  b"int (*rt28xx_close)(VOID *net_dev);",
                  b"int (*rt28xx_close)(VOID *net_dev);\n\tIN\tVOID *if_dev;", 1)
    path = output / "include/rt_os_net.h"
    replace_exact(path, b"VIRTUAL_IF_UP(VOID *pAd)",
                  b"VIRTUAL_IF_UP(VOID *pAd, VOID *if_dev)", 1)
    replace_exact(path, b"VIRTUAL_IF_DOWN(VOID *pAd)",
                  b"VIRTUAL_IF_DOWN(VOID *pAd, VOID *if_dev)", 1)
    replace_exact(path, b"{ rt28xx_open, rt28xx_close };",
                  b"{ rt28xx_open, rt28xx_close, if_dev };", 2)
    # Source staging includes generated host fixtures for main open/close.
    # Keep their substitute macros compatible with the new caller ABI.
    for rel, kind in (("check-main-open.c", "UP"),
                      ("check-main-close.c", "DOWN")):
        fixture = output / rel
        if fixture.exists():
            replace_exact(fixture, f"#define VIRTUAL_IF_{kind}(ad)".encode(),
                          f"#define VIRTUAL_IF_{kind}(ad, dev)".encode(), 1)
            replace_exact(fixture, f"VIRTUAL_IF_{kind}(pAd)".encode(),
                          f"VIRTUAL_IF_{kind}(pAd, net_dev)".encode(), 1)
    for rel, dev in CALLERS.items():
        data = (output / rel).read_bytes()
        for kind in ("UP", "DOWN"):
            call = f"VIRTUAL_IF_{kind}(pAd, {dev})".encode()
            if data.count(call) != 1:
                raise ValueError(f"candidate caller identity mismatch: {rel} {kind}")
    print(f"Prepared isolated caller-netdev ABI candidate: {output}")
    print("Request consumer still needs shared owner/generation validation.")


if __name__ == "__main__":
    main()
