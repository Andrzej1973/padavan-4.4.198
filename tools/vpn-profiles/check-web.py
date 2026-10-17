#!/usr/bin/env python3
"""Verify the read-only profile table is wired into a built tree."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tree", type=Path, help="Padavan tree root")
args = parser.parse_args()

web = (args.tree / "trunk/user/httpd/web_ex.c").read_text(encoding="utf-8")
page = (args.tree / "trunk/user/www/n56u_ribbon_fixed/vpncli.asp").read_text(encoding="utf-8")

assert (args.tree / "trunk/user/httpd/vpn-profiles-render.h").exists(), "render header not copied"
assert web.count("static int ej_wr_vpn_profile_rows") == 1, "profile rows handler missing"
assert web.count('{ "wr_vpn_profile_rows", ej_wr_vpn_profile_rows},') == 1, "handler not registered"
assert '"/usr/sbin/wr-vpn-profile"' in web, "fixed manager path changed"
assert page.count("<% wr_vpn_profile_rows(); %>") == 1, "page call missing"
assert "<#WRVPN_PROFILES_TITLE#>" in page, "page title key missing"

for name in ("EN.footer", "UK.dict", "RU.dict"):
    text = "\n" + (args.tree / "trunk/user/www/dict" / name).read_text(encoding="utf-8")
    for key in ("WRVPN_PROFILES_TITLE", "WRVPN_ID", "WRVPN_NAME", "WRVPN_REVISION"):
        assert f"\n{key}=" in text, (name, key)

print("PASS VPN profile table: handler, page call and dictionary keys are present")
