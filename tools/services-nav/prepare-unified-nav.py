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

GROUPS = (
    ("WRServicesNavDNS", (("WRServicesNavStubby", "Advanced_Services_DoT.asp", "CONFIG_FIRMWARE_INCLUDE_STUBBY"),
                           ("WRServicesNavDoH", "Advanced_Services_DoH.asp", "CONFIG_FIRMWARE_INCLUDE_DOH"))),
    ("WRServicesNavVPN", (("WRServicesNavWireGuard", "vpncli.asp", "CONFIG_FIRMWARE_INCLUDE_WIREGUARD"),
                           ("WRServicesNavZeroTier", "Advanced_zerotier.asp", "CONFIG_FIRMWARE_INCLUDE_ZEROTIER"),
                           ("WRServicesNavEoIP", "Advanced_Services_EoIP.asp", "CONFIG_FIRMWARE_INCLUDE_EOIP"))),
    ("WRServicesNavProxy", (("WRServicesNavShadowsocks", "Shadowsocks.asp", "CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS|CONFIG_FIRMWARE_INCLUDE_SSLOCAL|CONFIG_FIRMWARE_INCLUDE_SSREDIR"),
                              ("WRServicesNavPrivoxy", "Advanced_Services_Privoxy.asp", "CONFIG_FIRMWARE_INCLUDE_PRIVOXY"),
                              ("WRServicesNavWPAD", "Advanced_DHCP_Content.asp", "CONFIG_FIRMWARE_INCLUDE_WPAD"))),
    ("WRServicesNavAccess", (("WRServicesNavHTTP", "Advanced_Services_Content.asp#row_http_proto", None),
                               ("WRServicesNavSSH", "Advanced_Services_Content.asp#row_sshd", "CONFIG_FIRMWARE_INCLUDE_DROPBEAR|CONFIG_FIRMWARE_INCLUDE_OPENSSH"),
                               ("WRServicesNavTelnet", "Advanced_Services_Content.asp", None))),
    ("WRServicesNavDiagnostics", (("WRServicesNavIperf", "Advanced_Services_Content.asp#row_iperf3", "CONFIG_FIRMWARE_INCLUDE_IPERF3"),)),
    ("WRServicesNavSystem", (("WRServicesNavCron", "Advanced_Services_Content.asp", None),
                               ("WRServicesNavWatchdog", "Advanced_Services_Content.asp", None),
                               ("WRServicesNavDiscovery", "Advanced_Services_Content.asp", None))),
)


def read_config(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}


def enabled(config: set[str], capability: str | None) -> bool:
    return capability is None or any(f"{item}=y" in config for item in capability.split("|"))


def page_path(www: Path, route: str) -> Path:
    return www / route.split("#", 1)[0]


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
            links.append(f'<a class="wr-service-link" href="/{html.escape(route, quote=True)}"><#{label_key}#></a>')
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
.wr-service-link[aria-current="page"] { color:#fff; background:#0878c9; border-color:#0878c9; }
@media (max-width: 900px) { .wr-service-nav { grid-template-columns:repeat(2,minmax(0,1fr)); } }
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
})();
</script>
'''
    text = text.replace(anchor, anchor + "\n" + nav, 1)
    text = text.replace("</head>", css + "</head>", 1)
    text = text.replace("</body>", script + "</body>", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def verify(www: Path, config: set[str], *, image: bool = False) -> None:
    nav = rendered_groups(www, config)
    for name in ("Advanced_Services_Content.asp", "Advanced_Services_DoT.asp",
                 "Advanced_Services_DoH.asp", "Advanced_Services_Privoxy.asp",
                 "vpncli.asp", "Advanced_zerotier.asp", "Advanced_Services_EoIP.asp",
                 "Shadowsocks.asp", "Advanced_DHCP_Content.asp"):
        if not (www / name).is_file():
            continue
        text = (www / name).read_text(encoding="utf-8")
        if MARKER not in text or 'aria-label="<#WRServicesNav#>"' not in text:
            raise SystemExit(f"Unified navigation absent from {name}")
        if name == "Advanced_Services_Content.asp":
            legacy_links = ("stubby_settings_link", "privoxy_settings_link", "doh_settings_link")
            if any(link_id in text for link_id in legacy_links):
                raise SystemExit("Legacy DNS/Privoxy links remain outside the unified navigation")
            if "grid-template-columns:repeat(3,minmax(0,1fr))" not in text:
                raise SystemExit("Unified service navigation is missing its two-row desktop grid")
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
    pages = ["Advanced_Services_Content.asp"]
    for _, entries in GROUPS:
        for _, route, capability in entries:
            if not enabled(config, capability):
                continue
            name = route.split("#", 1)[0]
            if name not in pages and (www / name).is_file():
                pages.append(name)
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
    print("Prepared unified, capability-gated service navigation on " + ", ".join(pages))


if __name__ == "__main__":
    main()
