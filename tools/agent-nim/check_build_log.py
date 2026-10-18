#!/usr/bin/env python3
"""Exercise build_log against a small GitHub Actions log fixture."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_build_log.py PATH_TO_BUILD_LOG")
    binary = Path(sys.argv[1]).resolve()
    fixture = "\n".join([
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.420Z ##[group]Run python3 verify-image.py",
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.421Z parser.c:127: warning: format string contains Reader error: %s",
        'build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.422Z   fprintf(stderr, "Reader error: %s", message);',
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.423Z make[5]: Error 127 (ignored)",
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.424Z ##[endgroup]",
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.425Z SSH image check failed: refresh endpoint missing",
        "build (wr1200js)\tUNKNOWN STEP\t2026-10-18T06:16:15.426Z ##[error]Process completed with exit code 1.",
    ]) + "\n"
    with tempfile.TemporaryDirectory(prefix="build-log-check-") as temporary:
        root = Path(temporary)
        source = root / "fixture.log"
        report_path = root / "report.md"
        source.write_text(fixture, encoding="utf-8")
        subprocess.run(
            [str(binary), f"--input={source}", f"--out={report_path}", "--context=1"],
            check=True,
            capture_output=True,
            text=True,
        )
        report = report_path.read_text(encoding="utf-8")
    assert re.search(r"error markers: 1; retained groups: 1\.", report), report
    assert "SSH image check failed: refresh endpoint missing" in report, report
    assert "step: python3 verify-image.py" in report, report
    assert "warning:" not in report.lower(), report
    assert "Reader error:" not in report, report
    assert "Error 127 (ignored)" not in report, report
    print("PASS build_log ignores quoted warning/ignored errors and labels the failing command")


if __name__ == "__main__":
    main()
