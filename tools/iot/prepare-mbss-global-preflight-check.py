#!/usr/bin/env python3
"""Extract the isolated global preflight and MBSS_Remove into one host test."""
import argparse
from pathlib import Path


def function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise SystemExit(f"expected one reviewed {signature}")
    start = source.index(signature)
    end = source.index("\n}", start) + 2
    return source[start:end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("fixture output must be new")
    preflight = function(
        (args.driver / "include/wr-iot-mbss-global-preflight.inc").read_text(),
        "static inline INT wr_iot_mbss_global_preflight(RTMP_ADAPTER *pAd)")
    remove = function((args.driver / "ap/ap_mbss.c").read_bytes().decode("latin1"),
                      "INT MBSS_Remove(RTMP_ADAPTER *pAd)")
    template = Path(__file__).with_name(
        "mbss-global-preflight-host-fixture.c.in").read_text()
    for marker, value in (("@@MBSS_PREFLIGHT_FUNCTION@@", preflight),
                          ("@@MBSS_REMOVE_FUNCTION@@", remove)):
        if template.count(marker) != 1:
            raise SystemExit(f"expected one {marker}")
        template = template.replace(marker, value)
    args.output.write_text(template, encoding="utf-8")
    print("Extracted candidate preflight/remove; vendor and kernel operations injected")


if __name__ == "__main__":
    main()
