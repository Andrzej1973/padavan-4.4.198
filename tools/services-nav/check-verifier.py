#!/usr/bin/env python3
"""Exercise service navigation/image contracts without filesystem fixtures."""
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True

SCRIPT = Path(__file__).with_name("prepare-unified-nav.py")
spec = importlib.util.spec_from_file_location("services_nav", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("Cannot load unified navigation verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

complete = """<span role="status">state</span>
<script>var statuses = document.querySelectorAll('[role="status"]');
panel.appendChild(node);</script>
<style>.wr-service-status-panel:not(td) { background:#d9edf7; }
td.wr-service-status-panel { background:#d9edf7; }</style>"""
if module.status_panel_contract_error(complete) is not None:
    raise SystemExit("Verifier rejected a complete status-panel implementation")

for incomplete in (
    complete.replace("panel.appendChild(node);", ""),
    complete.replace(".wr-service-status-panel:not(td)", ".missing-panel"),
    complete.replace("td.wr-service-status-panel", ".missing-cell-panel"),
):
    if module.status_panel_contract_error(incomplete) is None:
        raise SystemExit("Verifier accepted an incomplete status-panel implementation")

optional = "CONFIG_FIRMWARE_INCLUDE_EOIP"
commented_config = module.parse_config(
    "# CONFIG_FIRMWARE_INCLUDE_EOIP=y\n"
    "CONFIG_FIRMWARE_INCLUDE_WPAD=n\n"
)
if module.enabled(commented_config, optional):
    raise SystemExit("Navigation treated a commented optional selector as enabled")
if module.enabled(commented_config, "CONFIG_FIRMWARE_INCLUDE_WPAD"):
    raise SystemExit("Navigation treated a disabled =n selector as enabled")
active_config = module.parse_config("CONFIG_FIRMWARE_INCLUDE_EOIP=y\n")
if not module.enabled(active_config, optional):
    raise SystemExit("Navigation ignored an active optional selector")

if module.add_back_link(
    '<nav id="wr_services_nav"><div class="wr-service-group">links</div></nav>'
).count('href="/Advanced_Services_Content.asp"') != 1:
    raise SystemExit("Service-page return link is missing from the expected navigation")

profile_tab = '<li><a href="/vpncli.asp"><#menu5_35_1#></a></li>'
if module.legacy_vpn_tab_contract_error("Advanced_zerotier.asp", profile_tab):
    raise SystemExit("Verifier rejected the protocol-selecting WireGuard/AmneziaWG link")
if module.legacy_vpn_tab_contract_error(
    "Advanced_zerotier.asp", '<a href="Advanced_wireguard.asp"><#menu5_35_1#></a>'
) is None:
    raise SystemExit("Verifier accepted the retired single-protocol VPN destination")
if module.legacy_vpn_tab_contract_error(
    "Advanced_wireguard.asp", '<li class="active">' + profile_tab.removeprefix("<li>")
) is None:
    raise SystemExit("Verifier accepted a selected tab that opens the retired legacy form")

for language, expected in module.VPN_TAB_LABELS.items():
    if module.legacy_vpn_label_contract_error(
        "menu5_35_1=" + expected + "\n", language
    ):
        raise SystemExit(f"Verifier rejected the {language} VPN tab label")
    if module.legacy_vpn_label_contract_error("menu5_35_1=WIREGUAED\n", language) is None:
        raise SystemExit(f"Verifier accepted the stale {language} VPN tab label")
    if module.legacy_vpn_label_contract_error(
        "menu5_35_1=WIREGUAED\nmenu5_35_1=" + expected + "\n", language
    ) is None:
        raise SystemExit(f"Verifier accepted a stale first {language} VPN tab label")
    if module.legacy_vpn_label_contract_error(
        "menu5_35_1=" + expected + "\nmenu5_35_1=" + expected + "\n", language
    ) is None:
        raise SystemExit(f"Verifier accepted duplicate {language} VPN tab labels")
    cleaned = module.upsert_single_dictionary_entry(
        ["menu5_35_1=WIREGUAED", "unrelated=value", "menu5_35_1=WIREGUAED"],
        "menu5_35_1",
        expected,
    )
    if cleaned != ["menu5_35_1=" + expected, "unrelated=value"]:
        raise SystemExit(f"Preparation failed to normalize duplicate {language} VPN labels")
    if module.legacy_vpn_label_contract_error("\n".join(cleaned), language):
        raise SystemExit(f"Prepared {language} VPN labels do not meet the image contract")

print("PASS service panels, active capability parsing, return links and VPN profile route")
