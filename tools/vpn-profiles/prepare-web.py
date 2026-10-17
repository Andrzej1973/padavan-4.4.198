#!/usr/bin/env python3
"""Add the read-only stored-profile table to the VPN client page."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tree", type=Path, help="Padavan tree root")
args = parser.parse_args()
here = Path(__file__).resolve().parent

httpd = args.tree / "trunk/user/httpd"
web = httpd / "web_ex.c"
page = args.tree / "trunk/user/www/n56u_ribbon_fixed/vpncli.asp"
text = web.read_text(encoding="utf-8")
html = page.read_text(encoding="utf-8")

if "wr_vpn_profile_rows" in text:
    raise RuntimeError("VPN profile rows already integrated")

mime_anchor = "struct mime_handler mime_handlers[] = {"
if text.count(mime_anchor) != 1:
    raise RuntimeError("mime_handlers anchor changed")
text = text.replace(mime_anchor, (here / "web/vpn-profiles.inc").read_text(encoding="utf-8") + "\n" + mime_anchor, 1)

ej_anchor = "struct ej_handler ej_handlers[] =\n{\n"
if text.count(ej_anchor) != 1:
    raise RuntimeError("ej_handlers anchor changed")
text = text.replace(ej_anchor, ej_anchor + '\t{ "wr_vpn_profile_rows", ej_wr_vpn_profile_rows},\n', 1)

footer_anchor = "    </form>"
if html.count(footer_anchor) != 1:
    raise RuntimeError("vpncli form anchor changed")
section = (here / "web/vpn-profiles-page.html").read_text(encoding="utf-8")
html = html.replace(footer_anchor, section + "\n" + footer_anchor, 1)

texts = {
    "EN.footer": (
        ("WRVPN_PROFILES_TITLE", "Stored VPN profiles"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Name"),
        ("WRVPN_REVISION", "Revision"),
    ),
    "UK.dict": (
        ("WRVPN_PROFILES_TITLE", "Збережені VPN-профілі"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Назва"),
        ("WRVPN_REVISION", "Ревізія"),
    ),
    "RU.dict": (
        ("WRVPN_PROFILES_TITLE", "Сохранённые VPN-профили"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Название"),
        ("WRVPN_REVISION", "Ревизия"),
    ),
}
for name, entries in texts.items():
    path = args.tree / "trunk/user/www/dict" / name
    existing = path.read_text(encoding="utf-8")
    missing = [f"{key}={value}" for key, value in entries if f"\n{key}=" not in "\n" + existing]
    if missing:
        path.write_text(existing.rstrip("\n") + "\n" + "\n".join(missing) + "\n",
                        encoding="utf-8", newline="\n")

web.write_text(text, encoding="utf-8", newline="\n")
page.write_text(html, encoding="utf-8", newline="\n")
print("PASS added the read-only stored-profile table to the VPN page")
