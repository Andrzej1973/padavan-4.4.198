#!/usr/bin/env python3
"""Extract the candidate's physical/main claimed dispatcher path for a host test."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    source = (args.candidate / "common/cmm_cfg.c").read_text(encoding="utf-8")
    start = source.index("if (claim.operation == WR_RADIO_START ||")
    end = source.index("valid = VIRTUAL_IF_NUM(pAd) > 0 &&", start)
    branch = source[start:end]
    required = ("wr_iot_virtual_main_open_claim_matches", "VIRTUAL_IF_INC(pAd)",
                "rt28xx_open(pAd->net_dev)", "VIRTUAL_IF_DEC(pAd)",
                "APMakeAllBssBeacon(pAd)", "virtual_up_stage = 2U")
    if any(branch.count(token) != 1 for token in required):
        parser.error("physical/main claimed branch changed")
    template = Path(__file__).with_name("main-open-dispatch-fixture.c.in").read_text(encoding="utf-8")
    if template.count("/* EXTRACTED_BRANCH */") != 1:
        parser.error("fixture insertion point changed")
    args.output.write_text(template.replace("/* EXTRACTED_BRANCH */", branch), encoding="utf-8")
    print(f"Extracted physical/main claimed dispatcher: {args.output}")


if __name__ == "__main__":
    main()
