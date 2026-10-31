#!/usr/bin/env python3
"""Apply and verify board-specific Wi-Fi capability policy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def require_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one {description}; found {count}.")
    return text.replace(old, new, 1)


def read_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("board") != "WR1200JS":
        raise SystemExit("This invocation is restricted to the WR1200JS policy.")
    feature = manifest.get("features", {}).get("transmit_beamforming_5ghz", {})
    if feature.get("status") != "unsupported" or feature.get("enabled") is not False:
        raise SystemExit("WR1200JS TXBF policy must remain explicitly unsupported/disabled.")
    mumimo = manifest.get("features", {}).get("multi_user_mimo_5ghz", {})
    if mumimo.get("status") != "unsupported" or mumimo.get("enabled") is not False:
        raise SystemExit("WR1200JS MU-MIMO policy must remain explicitly unsupported/disabled.")
    return feature


def prepare(root: Path, manifest_path: Path) -> None:
    feature = read_manifest(manifest_path)
    kernel_option = feature["kernel_option"]
    board_config = root / "trunk/configs/boards/WR1200JS/kernel-4.4.x.config"
    if not board_config.is_file():
        raise SystemExit(f"Missing board kernel config: {board_config}")
    config = board_config.read_text(encoding="utf-8")
    expected = f"# {kernel_option} is not set"
    if config.count(expected) != 1 or re.search(rf"^{re.escape(kernel_option)}=", config, re.M):
        raise SystemExit(f"{kernel_option} must be explicitly disabled in the board config.")

    web_ex_path = root / "trunk/user/httpd/web_ex.c"
    web_ex = web_ex_path.read_text(encoding="utf-8")
    web_ex = require_once(
        web_ex,
        "\tint has_5g_txbf = 1;",
        "\tint has_5g_txbf = 0;",
        "generic 5 GHz TXBF capability assignment",
    )
    web_ex_path.write_text(web_ex, encoding="utf-8", newline="")

    page_path = root / "trunk/user/www/n56u_ribbon_fixed/Advanced_WAdvanced_Content.asp"
    page = page_path.read_text(encoding="utf-8")
    page, rows_removed = re.subn(
        r"\s*<tr id=\"row_txbf\"(?=[\s>]).*?</tr>", "", page, count=1, flags=re.S
    )
    if rows_removed != 1:
        raise SystemExit("Expected exactly one TXBF WebUI row in Advanced_WAdvanced_Content.asp.")
    page, visibility_blocks_removed = re.subn(
        r'(?m)^[ \t]*if \(support_5g_txbf\(\)\)\r?\n'
        r'[ \t]*showhide_div\("row_txbf", 1\);[ \t]*\r?\n?',
        "",
        page,
        count=1,
    )
    if visibility_blocks_removed != 1:
        raise SystemExit("Expected exactly one TXBF WebUI visibility block.")

    page, mumimo_rows_removed = re.subn(
        r"\s*<tr id=\"row_mumimo\"(?=[\s>]).*?</tr>", "", page, count=1, flags=re.S
    )
    if mumimo_rows_removed != 1:
        raise SystemExit("Expected exactly one MU-MIMO WebUI row in Advanced_WAdvanced_Content.asp.")
    page, mumimo_blocks_removed = re.subn(
        r'(?m)^[ \t]*if \(support_5g_mumimo\(\)\)\r?\n'
        r'[ \t]*showhide_div\("row_mumimo", 1\);[ \t]*\r?\n?',
        "",
        page,
        count=1,
    )
    if mumimo_blocks_removed != 1:
        raise SystemExit("Expected exactly one MU-MIMO WebUI visibility block.")
    page_path.write_text(page, encoding="utf-8", newline="")

    variables_path = root / "trunk/user/httpd/variables.c"
    variables = variables_path.read_text(encoding="utf-8")
    variables = require_once(
        variables,
        '\t\t\t{"wl_txbf", "", NULL, EVM_RESTART_WIFI5},\n',
        "",
        "TXBF HTTP/NVRAM form variable",
    )
    variables_path.write_text(variables, encoding="utf-8", newline="")

    defaults_path = root / "trunk/user/shared/defaults.c"
    defaults = defaults_path.read_text(encoding="utf-8")
    defaults = require_once(
        defaults,
        '{ "wl_txbf", "1" },',
        '{ "wl_txbf", "0" },',
        "TXBF enabled default",
    )
    defaults_path.write_text(defaults, encoding="utf-8", newline="")
    print("WR1200JS TXBF unsupported policy applied: no WebUI row, no form variable, default off.")


def verify_image(root: Path, manifest_path: Path, report_path: Path) -> None:
    feature = read_manifest(manifest_path)
    kernel_config = root / "trunk/linux-4.4.x/.config"
    romfs_page = root / "trunk/romfs/www/Advanced_WAdvanced_Content.asp"
    defaults_path = root / "trunk/user/shared/defaults.c"
    variables_path = root / "trunk/user/httpd/variables.c"
    web_ex_path = root / "trunk/user/httpd/web_ex.c"

    config = kernel_config.read_text(encoding="utf-8")
    if config.count(f"# {feature['kernel_option']} is not set") != 1:
        raise SystemExit(f"Effective kernel config does not prove {feature['kernel_option']} disabled.")
    page = romfs_page.read_text(encoding="utf-8")
    if "row_txbf" in page or 'name="wl_txbf"' in page:
        raise SystemExit("Final ROMFS still exposes the unsupported TXBF control.")
    if "row_mumimo" in page or 'name="wl_mumimo"' in page:
        raise SystemExit("Final ROMFS still exposes the unsupported MU-MIMO control.")
    if "wl_txbf" in variables_path.read_text(encoding="utf-8"):
        raise SystemExit("HTTP variable table still accepts wl_txbf.")
    if '{ "wl_txbf", "0" }' not in defaults_path.read_text(encoding="utf-8"):
        raise SystemExit("TXBF default is not explicitly off.")
    if "int has_5g_txbf = 0;" not in web_ex_path.read_text(encoding="utf-8"):
        raise SystemExit("Generic 5 GHz TXBF capability is not disabled for this board build.")

    report = {
        "board": "WR1200JS",
        "feature": "transmit_beamforming_5ghz",
        "also_excluded": ["multi_user_mimo_5ghz"],
        "status": "unsupported",
        "evidence": "effective kernel config disabled; TXBF and MU-MIMO controls absent from final ROMFS; TXBF HTTP variable absent; default off",
        "runtime_verified": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"WR1200JS TXBF final-image policy verified; report: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Padavan source checkout")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verify-image", action="store_true")
    parser.add_argument("--report", type=Path, default=Path("wifi-capability-report.json"))
    args = parser.parse_args()
    if args.verify_image:
        verify_image(args.source_root, args.manifest, args.report)
    else:
        prepare(args.source_root, args.manifest)


if __name__ == "__main__":
    main()
