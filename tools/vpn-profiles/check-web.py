#!/usr/bin/env python3
"""Verify the read-only profile table is wired into a built tree."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tree", type=Path, help="Padavan tree root")
args = parser.parse_args()

web = (args.tree / "trunk/user/httpd/web_ex.c").read_text(encoding="utf-8")
page = (args.tree / "trunk/user/www/n56u_ribbon_fixed/vpncli.asp").read_text(encoding="utf-8")
httpd = (args.tree / "trunk/user/httpd/httpd.c").read_text(encoding="utf-8")

assert (args.tree / "trunk/user/httpd/vpn-profiles-render.h").exists(), "render header not copied"
assert web.count("static int ej_wr_vpn_profile_rows") == 1, "profile rows handler missing"
assert web.count('{ "wr_vpn_profile_rows", ej_wr_vpn_profile_rows},') == 1, "handler not registered"
assert web.count('{ "wr_vpn_token", ej_wr_vpn_token},') == 1, "token handler not registered"
assert web.count('{ "wr_vpn_action_state", ej_wr_vpn_action_state},') == 1, "state handler not registered"
assert web.count('{ "wr_vpn_action.cgi*", "application/json", no_cache_IE,') == 1, "action route missing"
assert '"/usr/sbin/wr-vpn-profile"' in web, "fixed manager path changed"
assert '"/usr/libexec/wrvpn/action-worker"' in web, "worker path changed"
assert httpd.count("int wr_vpn_request_is_post(void)") == 1, "POST helper missing"
assert page.count("<% wr_vpn_profile_rows(); %>") == 1, "page call missing"
assert "<#WRVPN_PROFILES_TITLE#>" in page, "page title key missing"
assert page.count("<% wr_vpn_token(); %>") == 1, "page token missing"
assert "wrVPNAct" in page and "wr_vpn_action.cgi" in page, "page action script missing"

script = re.search(r"//<!\[CDATA\[(.*?)//\]\]>", page, re.S)
assert script, "page action script block missing"
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
    handle.write(re.sub(r"<%.*?%>", '"asp"', script.group(1)))
    script_path = handle.name
try:
    subprocess.run(["node", "--check", script_path], check=True, capture_output=True)
finally:
    Path(script_path).unlink(missing_ok=True)

for name in ("EN.footer", "UK.dict", "RU.dict"):
    text = "\n" + (args.tree / "trunk/user/www/dict" / name).read_text(encoding="utf-8")
    for key in ("WRVPN_PROFILES_TITLE", "WRVPN_ID", "WRVPN_NAME", "WRVPN_REVISION"):
        assert f"\n{key}=" in text, (name, key)

print("PASS VPN profile table: handler, page call and dictionary keys are present")
