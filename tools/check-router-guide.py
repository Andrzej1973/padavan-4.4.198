#!/usr/bin/env python3
"""Validate that generated setup manuals retain required service guidance."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("text", type=Path)
    args = parser.parse_args()
    markdown = args.markdown.read_text(encoding="utf-8")
    text = args.text.read_text(encoding="utf-8")
    for value in (markdown, text):
        if "ZeroTier" not in value or "Stubby" not in value:
            raise SystemExit("guide lacks enabled ZeroTier or Stubby chapter")
        if "Не публікуйте" not in value:
            raise SystemExit("guide lacks credential-safety instruction")
    if "https://central.zerotier.com/" not in markdown:
        raise SystemExit("markdown guide lacks official ZeroTier Central link")
    if "dnsprivacy.org" not in markdown:
        raise SystemExit("markdown guide lacks official Stubby link")
    print("router guide checks passed")


if __name__ == "__main__":
    main()
