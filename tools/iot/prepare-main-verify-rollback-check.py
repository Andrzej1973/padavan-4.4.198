#!/usr/bin/env python3
"""Extract the staged main ndo_open into its checked-rollback host fixture."""
import argparse
from pathlib import Path


def extract(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError("main open signature is ambiguous")
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        if end >= len(source):
            raise ValueError("unbalanced main open")
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    source = (args.candidate / "os/linux/rt_main_dev.c").read_text(encoding="utf-8")
    actual = extract(source, "int MainVirtualIF_open(struct net_device *net_dev)")
    if actual.count("wr_iot_main_close_begin_checked(") != 1 or actual.count("wr_iot_main_readiness_verify(") != 1:
        parser.error("reviewed VERIFY rollback branch missing")
    template = Path(__file__).with_name("main-verify-rollback-fixture.c.in").read_text(encoding="utf-8")
    if template.count("/* ACTUAL_MAIN_OPEN */") != 1:
        parser.error("fixture marker changed")
    args.output.write_text(template.replace("/* ACTUAL_MAIN_OPEN */", actual), encoding="utf-8")
    print("Extracted actual main ndo_open VERIFY rollback fixture:", args.output)


if __name__ == "__main__":
    main()
