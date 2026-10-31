#!/usr/bin/env python3
"""Verify WR1200JS 2.4-GHz KVR code in the built kernel and shipped image."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

OPTIONS = ("CONFIG_MT7603E_DOT11R_FT_SUPPORT", "CONFIG_MT7603E_DOT11K_RRM_SUPPORT", "CONFIG_MT7603E_WNM_SUPPORT")
SYMBOLS = ("RRM_ReadParametersFromFile", "RRM_PeerNeighborReqAction",
           "WNM_ReadParametersFromFile", "PeerWNMAction", "WNMCtrlInit",
           "FT_rtmp_read_parameters_from_file", "FT_AuthReqHandler", "FT_AssocReqHandler")


def config_checks(text):
    lines = text.splitlines()
    return {key: lines.count(key + "=y") == 1 and ("# " + key + " is not set") not in lines for key in OPTIONS}


def require_mips_module(path):
    data = path.read_bytes()
    if len(data) < 52 or data[:7] != b"\x7fELF\x01\x01\x01" or struct.unpack_from("<HH", data, 16) != (1, 8):
        raise ValueError("Expected little-endian ELF32 MIPS relocatable module: " + str(path))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(tree, nm):
    trunk = tree / "trunk"
    kernel = trunk / "linux-4.4.x"
    config = kernel / ".config"
    checks = config_checks(config.read_text())
    checks["mt7603_ap_module_selected"] = "CONFIG_MT7603E_RLT_AP_SUPPORT=m" in config.read_text().splitlines()
    module = kernel / "drivers/net/wireless/mediatek/mt76x3_ap/mt76x3_ap.ko"
    result = {"model": "WR1200JS", "scope": "2.4-GHz compiled driver and ROMFS presence; k/v/r client behavior and interoperability unverified",
              "runtime_verified": False, "checks": checks, "required_symbols": list(SYMBOLS), "errors": []}
    result["kernel_config_sha256"] = digest(config)
    try:
        require_mips_module(module)
        checks["linked_module_mips_elf"] = True
        output = subprocess.check_output([nm, "--defined-only", str(module)], text=True, timeout=30)
        # Require executable code symbols, not undefined, data or incidental strings.
        defined = {parts[-1] for line in output.splitlines() if len(parts := line.split()) >= 3 and parts[-2] in ("T", "t")}
        result["missing_symbols"] = sorted(set(SYMBOLS) - defined)
        checks["kvr_code_linked"] = not result["missing_symbols"]
        result["linked_module_sha256"] = digest(module)
        shipped = list((trunk / "romfs/lib/modules").rglob("mt76x3_ap.ko"))
        checks["one_shipped_radio_module"] = len(shipped) == 1
        if len(shipped) == 1:
            require_mips_module(shipped[0])
            checks["shipped_module_mips_elf"] = True
            result["romfs_module_sha256"] = digest(shipped[0])
            shipped_output = subprocess.check_output([nm, "--defined-only", str(shipped[0])], text=True, timeout=30)
            shipped_symbols = {parts[-1] for line in shipped_output.splitlines() if len(parts := line.split()) >= 3 and parts[-2] in ("T", "t")}
            result["missing_shipped_symbols"] = sorted(set(SYMBOLS) - shipped_symbols)
            checks["shipped_kvr_code_linked"] = not result["missing_shipped_symbols"]
        source = (trunk / "user/rc/ralink.c").read_text()
        checks["single_rrm_record"] = source.count('"RRMEnable=') == 1
        checks["single_wnm_record"] = source.count('"WNMEnable=') == 1
        checks["single_kvr_emitter"] = source.count("WR_KVR_SINGLE_RECORD") == 1
        page = (trunk / "romfs/www/Advanced_WAdvanced2g_Content.asp").read_text()
        variables = (trunk / "user/httpd/variables.c").read_text()
        defaults = (trunk / "user/shared/defaults.c").read_text()
        httpd = (trunk / "romfs/usr/sbin/httpd").read_bytes()
        for key in ("rt_HT_80211KV", "rt_HT_80211R"):
            checks[key + "_control"] = 'name="' + key + '"' in page
            checks[key + "_backend"] = bool(re.search(r'\{\s*"' + key + r'"\s*,\s*""\s*,\s*NULL\s*,\s*EVM_RESTART_WIFI2\s*\}', variables)) and key.encode() in httpd
            checks[key + "_factory_off"] = re.findall(r'\{\s*"' + key + r'",\s*"([^"\n]*)"\s*\}', defaults) == ["0"]
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result["errors"].append(str(error))
    result["success"] = bool(checks) and all(checks.values()) and not result["errors"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--nm", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source, args.nm)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(("PASS" if result["success"] else "FAIL") + " WR1200JS 2.4 GHz KVR image gate; runtime remains unverified")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
