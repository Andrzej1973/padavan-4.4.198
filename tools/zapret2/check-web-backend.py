#!/usr/bin/env python3
"""Compile the generated Zapret2 HTTP handler with strict host diagnostics."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


STUBS = r"""
#define APP_ZAPRET2 1
#include <ctype.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#ifndef _WIN32
#include <sys/wait.h>
#else
#define WIFEXITED(status) (1)
#define WEXITSTATUS(status) (status)
#endif

typedef struct webs_stub { int unused; } *webs_t;
static int websWrite(webs_t wp, const char *format, ...)
{
 va_list args;
 (void)wp;
 va_start(args, format);
 vprintf(format, args);
 va_end(args);
 return 0;
}
static const char *nvram_get(const char *name)
{
 (void)name;
 return "";
}
static int nvram_get_int(const char *name)
{
 (void)name;
 return 0;
}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="prepared Padavan tree root")
    args = parser.parse_args()
    source_path = args.tree / "trunk/user/httpd/web_ex.c"
    source = source_path.read_text(encoding="utf-8")
    start_marker = (
        "static int wr_process_present(const char *name);\n"
        "static int wr_zapret2_command_state"
    )
    end_marker = "\nstruct ej_handler ej_handlers[] =\n"
    if source.count(start_marker) != 1 or source.count(end_marker) != 1:
        raise SystemExit("Zapret2 backend extraction anchors changed")
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    handler = source[start:end]
    fixture = (
        STUBS
        + "\n"
        + handler
        + "\nstatic int wr_process_present(const char *name)"
          " { (void)name; return -1; }\n"
        + "int main(void) { return ej_wr_zapret2_status(0, (webs_t)0, 0, 0); }\n"
    )

    compiler = shutil.which("gcc") or shutil.which("cc")
    if not compiler:
        raise SystemExit("A host C compiler is required for the Zapret2 gate")
    with tempfile.TemporaryDirectory(prefix="wr-zapret2-c-") as temporary:
        fixture_path = Path(temporary) / "zapret2-backend.c"
        fixture_path.write_text(fixture, encoding="utf-8", newline="\n")
        completed = subprocess.run(
            [
                compiler,
                "-std=gnu99",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-fsyntax-only",
                str(fixture_path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    if completed.returncode != 0:
        raise SystemExit(
            "Zapret2 backend C syntax failed:\n"
            + (completed.stderr or completed.stdout)
        )
    print("PASS Zapret2 backend C syntax")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
