#!/usr/bin/env python3
"""Extract the actual staged recovery callback for RTNL interleaving checks."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    source = (args.candidate / "os/linux/rt_main_dev.c").read_text(encoding="utf-8")
    signature = "VOID wr_iot_main_recovery_work_fn(struct work_struct *work)"
    if source.count(signature) != 1:
        parser.error("recovery callback ambiguous")
    start = source.index(signature)
    opening = source.index("{", start)
    depth, end = 1, opening + 1
    while depth:
        if end >= len(source):
            parser.error("unbalanced callback")
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    actual = source[start:end]
    for call in ("rtnl_trylock()", "wr_iot_main_recovery_rtnl_unavailable(",
                 "wr_iot_main_recovery_execute(adapter)", "rtnl_unlock()"):
        if actual.count(call) != 1:
            parser.error("callback missing: " + call)
    template = Path(__file__).with_name("main-recovery-rtnl-fixture.c.in").read_text(encoding="utf-8")
    if template.count("/* ACTUAL_RECOVERY_CALLBACK */") != 1:
        parser.error("fixture marker changed")
    args.output.write_text(template.replace("/* ACTUAL_RECOVERY_CALLBACK */", actual), encoding="utf-8")
    print("Extracted staged recovery callback:", args.output)


if __name__ == "__main__":
    main()
