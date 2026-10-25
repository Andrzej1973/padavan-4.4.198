#!/usr/bin/env python3
"""Check the transformed Zapret2 Classic WebUI before target compilation."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def require(path: Path, markers: tuple[str, ...]) -> str:
    if not path.is_file():
        raise SystemExit(f"Zapret2 WebUI file is missing: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise SystemExit(f"Zapret2 WebUI markers missing in {path}: {missing}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="prepared Padavan tree root")
    parser.add_argument("--node", action="store_true",
                        help="also syntax-check the emitted browser script")
    args = parser.parse_args()
    user = args.tree / "trunk/user"

    common = require(
        user / "httpd/common.h",
        ("#define EVM_RESTART_ZAPRET2", "#define EVT_RESTART_ZAPRET2"),
    )
    if len(re.findall(r"1ULL\s*<<\s*56\b", common)) != 1:
        raise SystemExit("Zapret2 event bit 56 is missing or duplicated")

    require(
        user / "shared/cflags.mk",
        ("CONFIG_FIRMWARE_INCLUDE_ZAPRET2", "-DAPP_ZAPRET2"),
    )
    require(
        user / "shared/notify_rc.h",
        ('RCN_RESTART_ZAPRET2\t"restart_zapret2"',),
    )
    require(
        user / "shared/defaults.c",
        ('{ "zapret2_enable", "0" }',),
    )
    require(
        user / "httpd/variables.c",
        ('"zapret2_enable"', '"scripts.zapret2.args"',
         "EVM_RESTART_ZAPRET2", "RCN_RESTART_ZAPRET2"),
    )
    require(
        user / "rc/services.c",
        ("start_zapret2", "stop_zapret2", "restart_zapret2",
         'nvram_get_int("zapret2_enable")'),
    )
    require(
        user / "rc/rc.c",
        ("RCN_RESTART_ZAPRET2", "restart_zapret2", "WR_ZAPRET2_REAPPLY"),
    )
    require(
        user / "httpd/web_ex.c",
        ("found_app_zapret2", "ej_wr_zapret2_status",
         '"wr_zapret2_status"', '"nfqws2"', '"/etc/storage/zapret2.args"',
         "/usr/sbin/iptables", "POSTROUTING -o '%s' -j ZAPRET2",
         "-p tcp -j NFQUEUE --queue-num 200 --queue-bypass",
         "-p udp -j NFQUEUE --queue-num 200 --queue-bypass"),
    )

    page_path = (
        user / "www/n56u_ribbon_fixed/Advanced_Services_Content.asp"
    )
    page = require(
        page_path,
        (
            'id="zapret2_enable_on_of"',
            'name="scripts.zapret2.args"',
            'id="wr_zapret2_status"',
            "function validZapret2()",
            "validForm() && validZapret2()",
            "window.setInterval(wrZapret2Refresh, 30000)",
            "showhide_div('row_zapret2_strategy'",
        ),
    )
    if page.count('id="zapret2_enable_on_of"') != 1:
        raise SystemExit("Zapret2 toggle is duplicated")
    if page.count('<tr id="wr_zapret2_status_row">') != 1:
        raise SystemExit("Zapret2 observed-state row is duplicated")

    for filename in ("EN.footer", "UK.dict", "RU.dict"):
        require(
            user / "www/dict" / filename,
            ("WRZapret2Unknown=", "WRZapret2StrategyRequired=",
             "WRZapret2ObservedNote="),
        )

    if args.node:
        start = page.index("var wrZapret2StatusBusy")
        end = page.index("function applyRule", start)
        browser_script = re.sub(r"<#[^#]+#>", "label", page[start:end])
        node = shutil.which("node")
        if not node:
            raise SystemExit("Node.js is required for the emitted script check")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", encoding="utf-8", delete=False
        ) as script:
            script.write(browser_script)
            script_path = Path(script.name)
        try:
            completed = subprocess.run(
                [node, "--check", str(script_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if completed.returncode != 0:
                raise SystemExit(
                    "Zapret2 browser script syntax failed: "
                    + (completed.stderr or completed.stdout)
                )
        finally:
            script_path.unlink(missing_ok=True)

    print("PASS Zapret2 WebUI transformation and emitted script")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
