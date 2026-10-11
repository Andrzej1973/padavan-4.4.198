#!/usr/bin/env python3
"""Verify that the inherited backup/restore WebUI survives ROMFS packaging.

This is a source/image-presence check. It does not exercise CGI uploads or
prove that the page is visible for a particular authenticated session.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("romfs", type=Path)
parser.add_argument("report", type=Path)
args = parser.parse_args()

www = args.romfs / "www"
page_path = www / "Advanced_SettingBackup_Content.asp"
menu_path = www / "state.js"
page = page_path.read_text(encoding="utf-8", errors="replace") if page_path.is_file() else ""
menu = menu_path.read_text(encoding="utf-8", errors="replace") if menu_path.is_file() else ""

rows = (
    "row_nv_reset", "row_nv_backup", "row_nv_restore1", "row_nv_restore2",
    "row_st_reset", "row_st_backup", "row_st_restore1", "row_st_restore2",
)
handlers = (
    "restoreNVRAM", "saveSetting", "uploadSetting", "restoreStorage",
    "saveStorage", "uploadStorage",
)
tokens = (
    "Setting_factorydefault_itemname", "Setting_save_itemname",
    "Setting_upload_itemname", "Adm_Setting_nvram", "Adm_Setting_store",
    "Adm_Setting_store_backup", "CTL_restore", "CTL_onlysave", "CTL_upload",
)

checks = {
    "page_in_romfs": page_path.is_file(),
    "admin_menu_route": "Advanced_SettingBackup_Content.asp" in menu,
    "admin_section": "show_menu(5,7,5)" in page,
    "safe_login_gate_preserved": "if (login_safe())" in page,
    "backup_restore_rows": {name: f'id="{name}"' in page for name in rows},
    "backup_restore_handlers": {name: f"function {name}()" in page for name in handlers},
    "page_translation_tokens": {name: f"<{('#' + name + '#')}>" in page for name in tokens},
    "EN_UK_RU_translation_keys": {},
}

for lang in ("EN", "UK", "RU"):
    dictionary_path = www / f"{lang}.dict"
    dictionary = dictionary_path.read_text(encoding="utf-8", errors="replace") if dictionary_path.is_file() else ""
    checks["EN_UK_RU_translation_keys"][lang] = {
        "dictionary_exists": dictionary_path.is_file(),
        "keys_present": {name: any(line.startswith(name + "=") for line in dictionary.splitlines()) for name in tokens},
    }

report = {
    "scope": "ROMFS presence of inherited NVRAM and /etc/storage backup/restore controls; runtime visibility and CGI behavior are not verified",
    "checks": checks,
}
args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

failed = []
for key, value in checks.items():
    if isinstance(value, dict):
        if key == "EN_UK_RU_translation_keys":
            for lang, item in value.items():
                if not item["dictionary_exists"]:
                    failed.append(f"{lang}.dict")
                failed.extend(f"{lang}.dict:{name}" for name, present in item["keys_present"].items() if not present)
        else:
            failed.extend(f"{name}" for name, present in value.items() if not present)
    elif not value:
        failed.append(key)

if failed:
    raise SystemExit("Settings backup/restore image check failed: " + ", ".join(failed))
print("Settings backup/restore page, menu route, secure gate, actions and EN/UK/RU labels are present in ROMFS")
