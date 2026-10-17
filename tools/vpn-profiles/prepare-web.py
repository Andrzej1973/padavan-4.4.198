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

# The injected code includes this header from the httpd directory.
(httpd / "vpn-profiles-render.h").write_text(
    (here / "web/vpn-profiles-render.h").read_text(encoding="utf-8"),
    encoding="utf-8", newline="\n")

mime_anchor = "struct mime_handler mime_handlers[] = {"
if text.count(mime_anchor) != 1:
    raise RuntimeError("mime_handlers anchor changed")
injection = ((here / "web/vpn-profiles.inc").read_text(encoding="utf-8") + "\n" +
             (here / "web/vpn-profiles-action.inc").read_text(encoding="utf-8") + "\n" +
             (here / "web/vpn-profiles-export.inc").read_text(encoding="utf-8") + "\n")
text = text.replace(mime_anchor, injection + mime_anchor, 1)

ej_anchor = "struct ej_handler ej_handlers[] =\n{\n"
if text.count(ej_anchor) != 1:
    raise RuntimeError("ej_handlers anchor changed")
entries = ('\t{ "wr_vpn_profile_rows", ej_wr_vpn_profile_rows},\n'
           '\t{ "wr_vpn_token", ej_wr_vpn_token},\n'
           '\t{ "wr_vpn_action_state", ej_wr_vpn_action_state},\n')
text = text.replace(ej_anchor, ej_anchor + entries, 1)

route_anchor = '\t{ "update.cgi*",'
if text.count(route_anchor) != 1:
    raise RuntimeError("update.cgi route anchor changed")
route = ('\t{ "wr_vpn_action.cgi*", "application/json", no_cache_IE,\n'
         '\t  wr_vpn_action_input, wr_vpn_action_output, 1 },\n')
route += ('\t{ "wr_vpn_export.cgi*", "application/json", no_cache_IE,\n'
          '\t  wr_vpn_export_input, wr_vpn_export_output, 1 },\n')
text = text.replace(route_anchor, route + route_anchor, 1)

main_path = httpd / "httpd.c"
main = main_path.read_text(encoding="utf-8")
method_anchor = "\tquery = file;"
if main.count(method_anchor) != 1 or "wr_vpn_request_is_post" in main:
    raise RuntimeError("httpd method anchor changed")
main = main.replace(method_anchor,
                    "\twr_vpn_method_post = (method_id == HTTP_METHOD_POST);\n" + method_anchor, 1)
include_anchor = "#include <stdio.h>"
if main.count(include_anchor) != 1:
    raise RuntimeError("httpd include anchor changed")
main = main.replace(include_anchor,
                    include_anchor + "\nstatic int wr_vpn_method_post;\n"
                    "int wr_vpn_request_is_post(void) { return wr_vpn_method_post; }\n", 1)
main_path.write_text(main, encoding="utf-8", newline="\n")

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
print("PASS added the stored-profile table and action endpoint to the VPN page")
