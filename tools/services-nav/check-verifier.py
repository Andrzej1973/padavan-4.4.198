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
if not module.service_excluded("WRServicesNavWatchdog", {"watchdog_cpu"}):
    raise SystemExit("WR1200JS unsupported CPU watchdog navigation was not excluded")
if module.service_excluded("WRServicesNavCron", {"watchdog_cpu"}):
    raise SystemExit("CPU watchdog exclusion suppressed an unrelated service")

dns_config = module.parse_config("CONFIG_FIRMWARE_INCLUDE_STUBBY=y\n")
tabs = module.service_tabs(dns_config, "Advanced_Services_DoT.asp")
catalog_tab = f'<li><a href="/{module.CATALOG}"><#WRServicesNavCatalog#></a></li>'
if not tabs.startswith('<ul class="nav nav-tabs wr-service-tabs">' + catalog_tab):
    raise SystemExit("Catalog must replace the first service tab")
if 'Advanced_Services_Content.asp' in tabs:
    raise SystemExit("The duplicate System tab must not appear")
if tabs.count('aria-current="page"') != 1:
    raise SystemExit("Service tabs must mark exactly one current page")
if 'href="/Advanced_Services_DoT.asp" aria-current="page"' not in tabs:
    raise SystemExit("Stubby must be the selected tab on its own page")
if 'Advanced_Services_DoH.asp' in tabs or 'Advanced_Services_Privoxy.asp' in tabs:
    raise SystemExit("Disabled services must not appear as tabs")
if module.service_tabs(dns_config, module.CATALOG):
    raise SystemExit("The services catalog must not duplicate the settings tabs")

profile_tab = '<li><a href="/vpncli.asp"><#menu5_35_1#></a></li>'
server_tab = '<li><a href="/vpnsrv.asp"><#WRServicesNavVPNServerTab#></a></li>'
if module.legacy_vpn_tab_contract_error("Advanced_zerotier.asp", profile_tab) is None:
    raise SystemExit("Verifier accepted absent VPN server navigation")
if module.legacy_vpn_tab_contract_error("Advanced_zerotier.asp", profile_tab + server_tab):
    raise SystemExit("Verifier rejected the protocol-selecting WireGuard/AmneziaWG link")
if module.legacy_vpn_tab_contract_error(
    "Advanced_zerotier.asp", '<a href="Advanced_wireguard.asp"><#menu5_35_1#></a>'
) is None:
    raise SystemExit("Verifier accepted the retired single-protocol VPN destination")
if module.legacy_vpn_tab_contract_error(
    "Advanced_wireguard.asp", '<li class="active">' + profile_tab.removeprefix("<li>") + server_tab
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

from tempfile import TemporaryDirectory

with TemporaryDirectory() as scratch:
    page = Path(scratch) / module.CATALOG
    page.write_text('<html><head></head><body><div id="TopBanner"></div><div id="wr_service_catalog"></div></body></html>', encoding="utf-8")
    for name in ("Advanced_Services_Content.asp", "vpncli.asp", "vpnsrv.asp"):
        (page.parent / name).touch()
    nav = module.rendered_groups(page.parent, set())
    module.inject(page, nav)
    themed = page.read_text(encoding="utf-8")
    assert 'class="well wr-service-nav"' in themed
    assert 'class="btn btn-mini btn-primary wr-service-link' in themed
    assert 'alert alert-info wr-service-status-panel' in themed
    assert 'background:#' not in themed

    vpn = page.parent / "vpnsrv.asp"
    vpn.write_text('<html><head></head><body><div id="TopBanner"></div></body></html>', encoding="utf-8")
    module.inject(vpn, nav)
    assert module.MARKER not in vpn.read_text(encoding="utf-8")

    zerotier = page.parent / "Advanced_zerotier.asp"
    zerotier.write_text(
        '<html><head><title>ASUS Wireless Router - <#menu5_32#></title></head>'
        '<body><div id="TopBanner"></div>'
        '<h2 class="box_head round_top">Tunnels - <#menu5_32#></h2>'
        '<a href="Advanced_zerotier.asp"><#menu5_32_1#></a>'
        '<table><tr><th><#running_status#></th></tr></table></body></html>',
        encoding="utf-8",
    )
    module.inject(zerotier, nav)
    rendered = zerotier.read_text(encoding="utf-8")
    assert '<h2 class="box_head round_top"><#WRServicesNavTunnels#></h2>' in rendered
    assert '><#WRServicesNavZeroTier#></a>' in rendered
    assert '<th><#WRServicesNavStatus#></th>' in rendered
    assert '<#menu5_32' not in rendered

with TemporaryDirectory() as scratch:
    www = Path(scratch)
    help_script = '<script type="text/javascript" src="/help.js"></script>\n'
    extra_script = '<script type="text/javascript" src="/help_b.js"></script>\n'
    pages = [www / name for name in ("Advanced_wireguard.asp", "Advanced_zerotier.asp")]
    for asset_present in (False, True):
        if asset_present:
            (www / "help_b.js").touch()
        for page in pages:
            page.write_text(help_script + extra_script, encoding="utf-8")
        module.prepare_legacy_vpn_tabs(www, set())
        expected = help_script + (extra_script if asset_present else "")
        assert all(page.read_text(encoding="utf-8") == expected for page in pages)

print("PASS service panels, board-specific exclusions, active capability parsing, return links and VPN profile route")
