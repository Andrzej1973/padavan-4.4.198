#!/usr/bin/env python3
"""Stage a source-pinned monitor identity correction outside production."""

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = "45a7ad61e18a9322cb5895eb327a671b99a0000b59941f5d9b58ce421c3ac44a"
RELATIVE = Path("sniffer/sniffer_radiotap.c")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() or output == source or source in output.parents:
        parser.error("output must be a new separate directory")
    raw = (source / RELATIVE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        parser.error("unreviewed monitor source bytes")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    start = text.index("BOOLEAN Monitor_Open(RTMP_ADAPTER *pAd, PNET_DEV dev_p)")
    end = text.index("BOOLEAN Monitor_Close(", start)
    original = text[start:end]
    old_tail = "\t}\n\n\treturn TRUE;\n}\n"
    if original.count(old_tail) != 1:
        parser.error("monitor-open identity/return anchor changed")
    revised = original.replace(old_tail, "\t\treturn TRUE;\n\t}\n\n\treturn FALSE;\n}\n")
    target = output / RELATIVE
    target.parent.mkdir(parents=True)
    patched = (text[:start] + revised + text[end:]).replace("\n", newline).encode("utf-8")
    target.write_bytes(patched)

    # Compile the exact extracted function with tiny host stand-ins so both
    # identity branches execute. This does not stand in for a MIPS driver build.
    fixture = """#include <assert.h>
typedef int BOOLEAN;
typedef void *PNET_DEV;
typedef struct { struct { struct { PNET_DEV if_dev; } monitor_wdev; } monitor_ctrl; } RTMP_ADAPTER;
#define TRUE 1
#define FALSE 0
#define ARPHRD_IEEE80211_RADIOTAP 803
static int type_sets;
#define RTMP_OS_NETDEV_SET_TYPE(dev, type) ((void)(dev), (void)(type), ++type_sets)
""" + revised + """
int main(void) {
    int expected = 0, other = 0;
    RTMP_ADAPTER adapter = {0};
    adapter.monitor_ctrl.monitor_wdev.if_dev = &expected;
    assert(Monitor_Open(&adapter, &other) == FALSE);
    assert(type_sets == 0);
    assert(Monitor_Open(&adapter, &expected) == TRUE);
    assert(type_sets == 1);
    return 0;
}
"""
    (output / "check-monitor-open.c").write_text(fixture, encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps({
        "production_installed": False,
        "source_path": RELATIVE.as_posix(),
        "original_sha256": EXPECTED_SHA256,
        "candidate_sha256": hashlib.sha256(patched).hexdigest(),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared isolated monitor identity candidate: {output}")


if __name__ == "__main__":
    main()
