#!/usr/bin/env python3
"""Extract partial main ndo_stop into a strict host ownership fixture."""

import argparse
from pathlib import Path


def function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError("ambiguous function: " + signature)
    start = source.index(signature)
    opening = source.index("{", start)
    depth, end = 1, opening + 1
    while depth:
        if end >= len(source):
            raise ValueError("unterminated function: " + signature)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    here = Path(__file__).resolve().parent
    if args.candidate:
        source = (args.candidate / "os/linux/rt_main_dev.c").read_text(encoding="utf-8")
    else:
        source = (here / "main-close-checked.inc").read_text(encoding="utf-8")
    helper = function(source, "static int wr_iot_main_close_continue_checked(")
    begin = function(source, "static int wr_iot_main_close_begin_checked(")
    preclose = function(source, "static int wr_iot_main_close_preclose_once(")
    close = function(source, "int MainVirtualIF_close(IN struct net_device *net_dev)")
    worker = function(source, "static int wr_iot_main_recovery_execute(")
    required = ("wr_iot_main_close_begin_checked",
                "wr_iot_main_close_preclose_once",
                "wr_iot_main_close_continue_checked", "RT_MOD_DEC_USE_COUNT()")
    if any(close.count(token) != 1 for token in required):
        parser.error("main close source changed")
    if any(begin.count(token) != 1 for token in
           ("wr_iot_main_stop_request", "wr_iot_ref_begin_close",
            "wr_iot_main_close_claim_preclose")):
        parser.error("shared close admission changed")
    if any(preclose.count(token) != 1 for token in
           ("RTMPInfClose", "wr_iot_main_close_claim_void_preclose",
            "wr_iot_main_close_finish_preclose")):
        parser.error("shared preclose changed")
    if any(helper.count(token) != 1 for token in
           ("wr_iot_main_close_receipt_matches", "wr_iot_virtual_down_checked",
            "wr_iot_main_stop_complete")):
        parser.error("shared close continuation changed")
    if any(worker.count(token) != 1 for token in
           ("wr_iot_main_recovery_begin", "wr_iot_main_recovery_bind_close",
            "wr_iot_main_recovery_mark_completed", "wr_iot_main_recovery_retain",
            "wr_iot_main_close_continue_checked")):
        parser.error("deferred close executor changed")
    template = (here / "main-close-host-fixture.c.in").read_text(encoding="utf-8")
    if template.count("/* EXTRACTED_MAIN_CLOSE */") != 1:
        parser.error("fixture insertion point changed")
    args.output.write_text(template.replace("/* EXTRACTED_MAIN_CLOSE */",
                                            helper + "\n\n" + begin + "\n\n" +
                                            preclose + "\n\n" + close + "\n\n" + worker),
                           encoding="utf-8")
    print(f"Extracted partial main ndo_stop: {args.output}")


if __name__ == "__main__":
    main()
