#!/usr/bin/env python3
"""Remove shadowing and duplicate KVR records from the pinned RC generator."""
import argparse
from pathlib import Path


def transform(text):
    if "WR_KVR_SINGLE_RECORD" in text:
        raise ValueError("KVR generator already prepared")
    for key in ("RRMEnable", "WNMEnable"):
        old = '\tfprintf(fp, "' + key + '=%d\\n", 0);\n'
        if text.count(old) != 1:
            raise ValueError("Pinned zero-default anchor changed: " + key)
        text = text.replace(old, "", 1)
    start = text.index("\t//802.11KVR\n")
    end = text.index("\t//HT_GI\n", start)
    block = text[start:end]
    if block.count("//802.11KVR") != 2 or block.count('"RRMEnable=') != 2:
        raise ValueError("Pinned duplicated KVR block changed")
    first = block[:block.index("\t//802.11KVR\n", 1)]
    # Both DBDC format strings require two arguments, one per BSS.
    first = first.replace('"FtSupport=%d;%d\\n",i_val);',
                          '"FtSupport=%d;%d\\n",i_val,i_val);')
    first = first.replace("//802.11KVR", "/* WR_KVR_SINGLE_RECORD: one authoritative value per key. */", 1)
    text = text[:start] + first + text[end:]
    for key in ("RRMEnable", "WNMEnable"):
        if text.count('"' + key + '=') != 1:
            raise ValueError("KVR key is still ambiguous: " + key)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    path = args.source / "trunk/user/rc/ralink.c"
    result = transform(path.read_text(encoding="utf-8"))
    path.write_text(result, encoding="utf-8", newline="")
    print("KVR generator: removed shadowing zero defaults and duplicate records")


if __name__ == "__main__":
    main()
