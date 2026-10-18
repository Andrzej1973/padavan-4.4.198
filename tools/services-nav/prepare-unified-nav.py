#!/usr/bin/env python3
"""Add one capability-gated, localized service navigation to supported pages.

The navigation is only a set of direct links. Existing ASP forms, apply handlers
and service lifecycles remain owned by their existing pages.
"""
import argparse
import html
from pathlib import Path
import re

MARKER = 'id="wr_services_nav"'
KEYS = {
    "WRServicesNav": ("Router services", "Служби маршрутизатора", "Службы маршрутизатора"),
    "WRServicesNavDNS": ("DNS", "DNS", "DNS"),
    "WRServicesNavVPN": ("VPN", "VPN", "VPN"),
    "WRServicesNavProxy": ("Proxy", "Проксі", "Прокси"),
    "WRServicesNavAccess": ("Access", "Доступ", "Доступ"),
    "WRServicesNavDiagnostics": ("Diagnostics", "Діагностика", "Диагностика"),
    "WRServicesNavSystem": ("System", "Система", "Система"),
    "WRServicesNavBack": ("← Services", "← Служби", "← Службы"),
    "WRServicesNavStubby": ("Stubby / DNS-over-TLS", "Stubby / DNS-over-TLS", "Stubby / DNS-over-TLS"),
    "WRServicesNavDoH": ("DNS-over-HTTPS", "DNS-over-HTTPS", "DNS-over-HTTPS"),
    "WRServicesNavWireGuard": ("WireGuard / AmneziaWG profiles", "Профілі WireGuard / AmneziaWG", "Профили WireGuard / AmneziaWG"),
    "WRServicesNavZeroTier": ("ZeroTier", "ZeroTier", "ZeroTier"),
    "WRServicesNavEoIP": ("EoIP", "EoIP", "EoIP"),
    "WRServicesNavShadowsocks": ("Shadowsocks", "Shadowsocks", "Shadowsocks"),
    "WRServicesNavPrivoxy": ("Privoxy", "Privoxy", "Privoxy"),
    "WRServicesNavWPAD": ("WPAD / PAC", "WPAD / PAC", "WPAD / PAC"),
    "WRServicesNavHTTP": ("HTTP / HTTPS", "HTTP / HTTPS", "HTTP / HTTPS"),
    "WRServicesNavSSH": ("SSH", "SSH", "SSH"),
    "WRServicesNavTelnet": ("Telnet", "Telnet", "Telnet"),
    "WRServicesNavIperf": ("iPerf3", "iPerf3", "iPerf3"),
    "WRServicesNavCron": ("Cron", "Cron", "Cron"),
    "WRServicesNavWatchdog": ("Watchdog", "Watchdog", "Watchdog"),
    "WRServicesNavDiscovery": ("Network discovery", "Виявлення пристроїв", "Обнаружение устройств"),
}
VPN_TAB_LABELS = {
    "EN": "WireGuard / AmneziaWG profiles",
    "UK": "Профілі WireGuard / AmneziaWG",
    "RU": "Профили WireGuard / AmneziaWG",
}

GROUPS = (
    ("WRServicesNavDNS", (("WRServicesNavStubby", "Advanced_Services_DoT.asp", "CONFIG_FIRMWARE_INCLUDE_STUBBY"),
                           ("WRServicesNavDoH", "Advanced_Services_DoH.asp", "CONFIG_FIRMWARE_INCLUDE_DOH"))),
    ("WRServicesNavVPN", (("WRServicesNavWireGuard", "vpncli.asp", "CONFIG_FIRMWARE_INCLUDE_WIREGUARD"),
                           ("WRServicesNavZeroTier", "Advanced_zerotier.asp", "CONFIG_FIRMWARE_INCLUDE_ZEROTIER"),
                           ("WRServicesNavEoIP", "Advanced_Services_EoIP.asp", "CONFIG_FIRMWARE_INCLUDE_EOIP"))),
    ("WRServicesNavProxy", (("WRServicesNavShadowsocks", "Shadowsocks.asp", "CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS|CONFIG_FIRMWARE_INCLUDE_SSLOCAL|CONFIG_FIRMWARE_INCLUDE_SSREDIR"),
                              ("WRServicesNavPrivoxy", "Advanced_Services_Privoxy.asp", "CONFIG_FIRMWARE_INCLUDE_PRIVOXY"),
                              ("WRServicesNavWPAD", "Advanced_DHCP_Content.asp#row_wpad", "CONFIG_FIRMWARE_INCLUDE_WPAD"))),
    ("WRServicesNavAccess", (("WRServicesNavHTTP", "Advanced_Services_Content.asp#row_http_proto", None),
                               ("WRServicesNavSSH", "Advanced_Services_Content.asp#row_sshd", "CONFIG_FIRMWARE_INCLUDE_DROPBEAR|CONFIG_FIRMWARE_INCLUDE_OPENSSH"),
                               ("WRServicesNavTelnet", "Advanced_Services_Content.asp#telnetd_on_of", None))),
    ("WRServicesNavDiagnostics", (("WRServicesNavIperf", "Advanced_Services_Content.asp#row_iperf3", "CONFIG_FIRMWARE_INCLUDE_IPERF3"),)),
    ("WRServicesNavSystem", (("WRServicesNavCron", "Advanced_Services_Content.asp#crond_enable_on_of", None),
                               ("WRServicesNavWatchdog", "Advanced_Services_Content.asp#watchdog_cpu_on_of", None),
                               ("WRServicesNavDiscovery", "Advanced_Services_Content.asp#lltd_enable_on_of", None))),
)


def parse_config(text: str) -> set[str]:
    """Return active assignments only; commented selectors are disabled."""
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    }


def read_config(path: Path) -> set[str]:
    return parse_config(path.read_text(encoding="utf-8"))


def enabled(config: set[str], capability: str | None) -> bool:
    return capability is None or any(f"{item}=y" in config for item in capability.split("|"))


def page_path(www: Path, route: str) -> Path:
    return www / route.split("#", 1)[0]


def add_back_link(nav: str) -> str:
    return (
        nav.rsplit("</div>", 1)[0]
        + '<a class="wr-service-link wr-service-link--back" '
        'href="/Advanced_Services_Content.asp"><#WRServicesNavBack#></a>'
        '</div></nav>'
    )


def rendered_groups(www: Path, config: set[str]) -> str:
    chunks = []
    for heading, entries in GROUPS:
        links = []
        for label_key, route, capability in entries:
            if not enabled(config, capability):
                continue
            target = page_path(www, route)
            if not target.is_file():
                if enabled(config, capability):
                    raise SystemExit(f"Enabled service route is missing: {route}")
                continue
            separate = label_key in {"WRServicesNavStubby", "WRServicesNavDoH", "WRServicesNavPrivoxy"}
            new_context = ' target="_blank" rel="noopener noreferrer"' if separate else ""
            link_class = "wr-service-link wr-service-link--new-context" if separate else "wr-service-link"
            links.append(f'<a class="{link_class}" href="/{html.escape(route, quote=True)}"{new_context}><#{label_key}#></a>')
        if links:
            chunks.append('<div class="wr-service-group"><strong><#' + heading + '#></strong>' + "".join(links) + "</div>")
    if not chunks:
        raise SystemExit("No supported services were found for the unified navigation")
    return (
        f'<nav {MARKER} aria-label="<#WRServicesNav#>" class="wr-service-nav">'
        + "".join(chunks) + "</nav>"
    )


def inject(path: Path, nav: str) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        raise SystemExit(f"Unified service navigation was already inserted: {path.name}")
    anchor = '<div id="TopBanner"></div>'
    if text.count(anchor) != 1 or text.count("</head>") != 1 or text.count("</body>") != 1:
        raise SystemExit(f"Unexpected service-page structure: {path.name}")
    css = '''
<style>
.wr-service-nav { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px 10px; margin:6px 0 8px; padding:8px; background:#f4f4f4; border:1px solid #ddd; }
.wr-service-group { display:flex; min-width:0; flex-wrap:wrap; align-items:center; gap:5px; padding:3px 6px; border-right:1px solid #ccc; }
.wr-service-group strong { color:#555; margin-right:3px; }
.wr-service-link { display:inline-block; padding:4px 7px; border:1px solid #ccc; border-radius:3px; background:#fff; white-space:nowrap; }
.wr-service-link--new-context { padding:3px 6px; font-size:12px; }
.wr-service-link--back { color:#fff; background:#0878c9; border-color:#0878c9; }
.wr-service-link[aria-current="page"] { color:#fff; background:#0878c9; border-color:#0878c9; }
td.wr-service-status-panel { background:#d9edf7 !important; border:1px solid #bce8f1 !important; border-radius:4px; padding:10px !important; }
.wr-service-status-panel:not(td) { box-sizing:border-box; margin:6px 0; padding:10px; color:#31708f; background:#d9edf7; border:1px solid #bce8f1; border-radius:4px; }
.wr-service-status-panel:not(td) .help-block { margin:6px 0 0; color:#31708f; }
@media (max-width: 760px) { .wr-service-nav { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width: 520px) { .wr-service-nav { grid-template-columns:minmax(0,1fr); } .wr-service-group { border-right:0; } }
</style>
'''
    script = '''
<script type="text/javascript">
(function(){
  var here = window.location.pathname + window.location.hash;
  var links = document.querySelectorAll('#wr_services_nav a');
  for (var i = 0; i < links.length; i++) {
    if (links[i].pathname + links[i].hash === here) {
      links[i].setAttribute('aria-current', 'page');
      break;
    }
  }
  var statuses = document.querySelectorAll('[role="status"]');
  for (var j = 0; j < statuses.length; j++) {
    var node = statuses[j], cell = node.parentNode;
    while (cell && cell.tagName && cell.tagName.toLowerCase() !== 'td') cell = cell.parentNode;
    if (cell) cell.className += (cell.className ? ' ' : '') + 'wr-service-status-panel';
    else {
      var ancestor = node.parentNode, alreadyGrouped = false;
      while (ancestor && ancestor.tagName) {
        if (/(^|\\s)wr-service-status-panel(\\s|$)/.test(ancestor.className || '')) { alreadyGrouped = true; break; }
        ancestor = ancestor.parentNode;
      }
      if (alreadyGrouped) continue;
      var parent = node.parentNode, panel = document.createElement('div');
      panel.className = 'wr-service-status-panel';
      parent.insertBefore(panel, node);
      panel.appendChild(node);
      var next = panel.nextSibling;
      while (next) {
        var tag = next.nodeType === 1 ? next.tagName.toLowerCase() : '';
        var help = tag === 'p' && /(^|\\s)help-block(\\s|$)/.test(next.className || '');
        var small = tag === 'small';
        var button = tag === 'button';
        if (next.nodeType === 3 && !next.nodeValue.trim()) {
          var whitespace = next; next = next.nextSibling; panel.appendChild(whitespace); continue;
        }
        if (help || small || button) {
          var grouped = next; next = next.nextSibling; panel.appendChild(grouped); continue;
        }
        break;
      }
    }
  }
})();
</script>
'''
    if path.name != "Advanced_Services_Content.asp":
        nav = add_back_link(nav)
    text = text.replace(anchor, anchor + "\n" + nav, 1)
    text = text.replace("</head>", css + "</head>", 1)
    text = text.replace("</body>", script + "</body>", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def prepare_legacy_vpn_tabs(www: Path, config: set[str]) -> None:
    """Point the inherited WireGuard tab to the actual WG/AWG profile UI."""
    zerotier = www / "Advanced_zerotier.asp"
    legacy = www / "Advanced_wireguard.asp"
    if not enabled(config, "CONFIG_FIRMWARE_INCLUDE_WIREGUARD"):
        return
    old = '<a href="Advanced_wireguard.asp"><#menu5_35_1#></a>'
    new = '<a href="/vpncli.asp"><#menu5_35_1#></a>'
    for path in (zerotier, legacy):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"Legacy VPN tab anchor changed in {path.name}")
        text = text.replace(old, new, 1)
        if path.name == "Advanced_wireguard.asp":
            active_tab = re.compile(r'<li class="active">(\s*' + re.escape(new) + r')')
            text, count = active_tab.subn(r'<li>\1', text, count=1)
            if count != 1:
                raise SystemExit("Legacy WireGuard active-tab anchor changed")
        path.write_text(text, encoding="utf-8", newline="\n")


def legacy_vpn_tab_contract_error(name: str, text: str) -> str | None:
    """Ensure inherited VPN tabs lead to the protocol-selecting profile page."""
    old = '<a href="Advanced_wireguard.asp"><#menu5_35_1#></a>'
    expected = '<a href="/vpncli.asp"><#menu5_35_1#></a>'
    if old in text:
        return "legacy tab still targets the single-protocol form"
    if expected not in text:
        return "protocol-selecting profile link is missing"
    if name == "Advanced_wireguard.asp" and re.search(
        r'<li class="active">\s*' + re.escape(expected), text
    ):
        return "retired single-protocol form is incorrectly marked as the selected tab"
    return None


def legacy_vpn_label_contract_error(dictionary: str, language: str) -> str | None:
    """Require one localized VPN tab value, matching httpd's first-match lookup."""
    expected = VPN_TAB_LABELS[language]
    values = [
        line.split("=", 1)[1]
        for line in dictionary.splitlines()
        if line.startswith("menu5_35_1=")
    ]
    if not values:
        return "menu5_35_1 translation is missing"
    if len(values) != 1:
        return f"menu5_35_1 has {len(values)} entries; expected exactly one"
    if values[0] != expected:
        return f"menu5_35_1 resolves to {values[0]!r}, expected {expected!r}"
    return None


def upsert_single_dictionary_entry(lines: list[str], key: str, value: str) -> list[str]:
    """Set one first-match dictionary value and remove duplicate definitions."""
    prefix = key + "="
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    entry = prefix + value
    if not matches:
        return [*lines, entry]
    first = matches[0]
    return [
        entry if index == first else line
        for index, line in enumerate(lines)
        if not line.startswith(prefix) or index == first
    ]


def status_panel_contract_error(text: str) -> str | None:
    """Return a missing runtime/style marker for service status panels."""
    if 'role="status"' not in text:
        return None
    required = (
        "document.querySelectorAll('[role=\"status\"]')",
        "wr-service-status-panel",
        "panel.appendChild(node)",
        ".wr-service-status-panel:not(td)",
        "td.wr-service-status-panel",
    )
    return next((marker for marker in required if marker not in text), None)


def verify(www: Path, config: set[str], *, image: bool = False) -> None:
    nav = rendered_groups(www, config)
    pages = ["Advanced_Services_Content.asp", "Advanced_Services_DoT.asp",
                 "Advanced_Services_DoH.asp", "Advanced_Services_Privoxy.asp",
                 "vpncli.asp", "Advanced_zerotier.asp", "Advanced_Services_EoIP.asp",
                 "Shadowsocks.asp", "Advanced_DHCP_Content.asp"]
    if enabled(config, "CONFIG_FIRMWARE_INCLUDE_WIREGUARD"):
        pages.append("Advanced_wireguard.asp")
    for name in pages:
        if not (www / name).is_file():
            continue
        text = (www / name).read_text(encoding="utf-8")
        if MARKER not in text or 'aria-label="<#WRServicesNav#>"' not in text:
            raise SystemExit(f"Unified navigation absent from {name}")
        marker_at = text.index(MARKER)
        nav_begin = text.rfind("<nav ", 0, marker_at)
        if nav_begin < 0 or "<" in text[nav_begin + len("<nav "):marker_at]:
            raise SystemExit(f"Unified navigation opening tag is invalid in {name}")
        nav_end = text.index("</nav>", nav_begin)
        nav_html = text[nav_begin:nav_end + len("</nav>")]
        expected_nav = nav if name == "Advanced_Services_Content.asp" else add_back_link(nav)
        if nav_html != expected_nav:
            raise SystemExit(
                f"Service navigation in {name} does not exactly match active build capabilities"
            )
        if name != "Advanced_Services_Content.asp":
            back = ('<a class="wr-service-link wr-service-link--back" '
                    'href="/Advanced_Services_Content.asp"><#WRServicesNavBack#></a>')
            if back not in nav_html:
                raise SystemExit(f"Same-tab return-to-services link is invalid in {name}")
        if name == "Advanced_DHCP_Content.asp":
            expected = 'href="/Advanced_DHCP_Content.asp#row_wpad"><#WRServicesNavWPAD#></a>'
            if expected not in text[text.index(MARKER):text.index("</nav>", text.index(MARKER))]:
                raise SystemExit("WPAD / PAC navigation must target the actual DHCP editor row")
        if status_panel_contract_error(text):
            raise SystemExit(f"Service status blue-panel grouping or styles absent from {name}")
        if enabled(config, "CONFIG_FIRMWARE_INCLUDE_WIREGUARD") and name in {
            "Advanced_zerotier.asp", "Advanced_wireguard.asp"
        }:
            error = legacy_vpn_tab_contract_error(name, text)
            if error:
                raise SystemExit(f"Legacy VPN submenu contract failed in {name}: {error}")
        if name == "Advanced_Services_Content.asp":
            legacy_links = ("stubby_settings_link", "privoxy_settings_link", "doh_settings_link")
            if any(link_id in text for link_id in legacy_links):
                raise SystemExit("Legacy DNS/Privoxy links remain outside the unified navigation")
            if "grid-template-columns:repeat(3,minmax(0,1fr))" not in text:
                raise SystemExit("Unified service navigation is missing its two-row desktop grid")
        if name == "Advanced_Services_Content.asp":
            for label_key, route in (
                ("WRServicesNavCron", "Advanced_Services_Content.asp#crond_enable_on_of"),
                ("WRServicesNavWatchdog", "Advanced_Services_Content.asp#watchdog_cpu_on_of"),
                ("WRServicesNavDiscovery", "Advanced_Services_Content.asp#lltd_enable_on_of"),
                ("WRServicesNavTelnet", "Advanced_Services_Content.asp#telnetd_on_of"),
            ):
                expected = f'href="/{route}"><#{label_key}#></a>'
                if expected not in nav_html:
                    raise SystemExit(f"{label_key} does not navigate to its service control")
        for link_id, route in (("WRServicesNavStubby", "Advanced_Services_DoT.asp"),
                               ("WRServicesNavDoH", "Advanced_Services_DoH.asp"),
                               ("WRServicesNavPrivoxy", "Advanced_Services_Privoxy.asp")):
            anchor = f'href="/{route}" target="_blank" rel="noopener noreferrer"><#{link_id}#></a>'
            if f'<#{link_id}#></a>' in nav_html and anchor not in nav_html:
                raise SystemExit(f"{link_id} must open its full page separately")
        for match in re.finditer(r'href="/([^"#]+)(?:#([^"]*))?"', text[text.index(MARKER):text.index("</nav>", text.index(MARKER))]):
            route, fragment = match.groups()
            target = www / route
            if not target.is_file():
                raise SystemExit(f"Navigation links to a missing route in {name}: {route}")
            if fragment:
                target_text = target.read_text(encoding="utf-8")
                anchor = re.compile(r'''\b(?:id|name)\s*=\s*(["'])''' + re.escape(fragment) + r'''\1''')
                if not anchor.search(target_text):
                    raise SystemExit(f"Navigation links to a missing anchor in {name}: {route}#{fragment}")
    for key in KEYS:
        for lang in ("EN.footer", "UK.dict", "RU.dict"):
            # EN.footer is a source fragment; the image build concatenates it
            # with EN.header into EN.dict before packing ROMFS.
            image_name = "EN.dict" if lang == "EN.footer" else lang
            dictionary = www / image_name if image else www / "dict" / lang
            if not dictionary.is_file() or not any(line.startswith(key + "=") for line in dictionary.read_text(encoding="utf-8").splitlines()):
                raise SystemExit(f"Missing {key} translation in {lang}")
    if enabled(config, "CONFIG_FIRMWARE_INCLUDE_WIREGUARD"):
        for language in ("EN", "UK", "RU"):
            dictionary = (www / f"{language}.dict").read_text(encoding="utf-8")
            error = legacy_vpn_label_contract_error(dictionary, language)
            if error:
                raise SystemExit(f"Legacy VPN tab label failed in {language}.dict: {error}")
    print("PASS unified service navigation routes, pages, and EN/UK/RU labels")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Padavan source tree or extracted ROMFS tree")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--verify-image", action="store_true")
    args = parser.parse_args()
    config = read_config(args.config)
    www = args.source / ("www" if args.verify_image else "trunk/user/www/n56u_ribbon_fixed")
    if not www.is_dir():
        raise SystemExit(f"Web root not found: {www}")
    if args.verify_image:
        verify(www, config, image=True)
        return
    nav = rendered_groups(www, config)
    prepare_legacy_vpn_tabs(www, config)
    pages = ["Advanced_Services_Content.asp"]
    for _, entries in GROUPS:
        for _, route, capability in entries:
            if not enabled(config, capability):
                continue
            name = route.split("#", 1)[0]
            if name not in pages and (www / name).is_file():
                pages.append(name)
    if enabled(config, "CONFIG_FIRMWARE_INCLUDE_WIREGUARD") and (www / "Advanced_wireguard.asp").is_file():
        pages.append("Advanced_wireguard.asp")
    for name in pages:
        inject(www / name, nav)
    dictionary_root = args.source / "trunk/user/www/dict"
    translations = {
        "EN.footer": 0,
        "UK.dict": 1,
        "RU.dict": 2,
    }
    for filename, language_index in translations.items():
        path = dictionary_root / filename
        content = path.read_text(encoding="utf-8")
        if any(line.split("=", 1)[0] in KEYS for line in content.splitlines() if "=" in line):
            raise SystemExit(f"Unified navigation translations already exist in {filename}")
        content = content.rstrip("\n") + "\n" + "\n".join(f"{key}={values[language_index]}" for key, values in KEYS.items()) + "\n"
        path.write_text(content, encoding="utf-8", newline="\n")
    # The inherited submenu label was misspelled "WIREGUAED" and linked to
    # the retired single-tunnel form. Keep the existing menu key, but make the
    # destination and label describe the full protocol-selecting profile UI.
    vpn_tab = {
        "EN.footer": VPN_TAB_LABELS["EN"],
        "UK.dict": VPN_TAB_LABELS["UK"],
        "RU.dict": VPN_TAB_LABELS["RU"],
    }
    for filename, value in vpn_tab.items():
        path = dictionary_root / filename
        lines = path.read_text(encoding="utf-8").splitlines()
        lines = upsert_single_dictionary_entry(lines, "menu5_35_1", value)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("Prepared unified, capability-gated service navigation on " + ", ".join(pages))


if __name__ == "__main__":
    main()
