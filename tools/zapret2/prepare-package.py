#!/usr/bin/env python3
"""Stage the Zapret2 nfqws2 package inside a Padavan tree."""

import argparse
import shutil
from pathlib import Path


MAKEFILE = """\
# Zapret2 nfqws2: single static binary built from the pinned snapshot.
ZAPRET_DIR := $(ROOTDIR)/user/zapret2

.PHONY: all romfs clean

all: nfqws2

nfqws2:
\tCC="$(CC)" CFLAGS="$(CFLAGS)" LDFLAGS="$(LDFLAGS)" \\
\t\t./build-nfqws2.sh "$(ROOTDIR)" "$@" deps

romfs:
\t@[ -x nfqws2 ] || { echo "nfqws2 was not built" >&2; exit 1; }
\tmkdir -p $(ROMFSDIR)/usr/sbin
\t$(ROMFSINST) -p +x nfqws2 /usr/sbin/nfqws2

clean:
\trm -f nfqws2
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Padavan tree root")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    repo = here.parents[1]
    tree = args.tree
    user = tree / "trunk/user"
    target = user / "zapret2"
    deps = target / "deps"
    nfq2 = target / "nfq2"

    if target.exists():
        raise SystemExit(f"package directory already exists: {target}")

    makefile = user / "Makefile"
    text = makefile.read_text(encoding="utf-8")
    anchor = "all: $(patsubst %,%_only,$(dir_y))"
    addition = (
        "# Zapret2 packet processor; only with the explicit selector.\n"
        "ifeq ($(CONFIG_FIRMWARE_INCLUDE_ZAPRET2),y)\n"
        "dir_y += zapret2\n"
        "endif\n\n"
    )
    if text.count(anchor) != 1 or "dir_y += zapret2" in text:
        raise SystemExit("user/Makefile anchor changed; no files written")

    target.mkdir(parents=True)
    deps.mkdir()
    shutil.copytree(repo / "third_party/bol-van/zapret2/nfq2", nfq2)
    for archive in (repo / "third_party/netfilter").glob("*.tar.bz2"):
        shutil.copyfile(archive, deps / archive.name)
    shutil.copyfile(here / "build-nfqws2.sh", target / "build-nfqws2.sh")
    (target / "build-nfqws2.sh").chmod(0o755)
    (target / "Makefile").write_text(MAKEFILE, encoding="utf-8", newline="\n")

    makefile.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8", newline="\n")
    print("PASS staged the Zapret2 nfqws2 package (selector still controls the image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
