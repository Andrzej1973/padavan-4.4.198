#!/usr/bin/env python3
"""Register Stubby build assets; service/backend/UI integration is separate."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil


def register(text, line, marker):
    if marker in text:
        raise RuntimeError("Existing registration requires inspection: " + marker)
    anchors = [item for item in text.splitlines(True) if item.startswith("all:")]
    if len(anchors) != 1:
        raise RuntimeError("Expected one all target")
    return text.replace(anchors[0], line + "\n\n" + anchors[0], 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path, help="Prepared Padavan checkout root")
    parser.add_argument("--config", required=True, type=Path, help="Requested firmware config")
    args = parser.parse_args()
    selections = [line.strip() for line in args.config.read_text(encoding="utf-8").splitlines()
                  if line.strip().startswith("CONFIG_FIRMWARE_INCLUDE_STUBBY=")]
    if selections != ["CONFIG_FIRMWARE_INCLUDE_STUBBY=y"]:
        raise RuntimeError("Integration requires one explicit Stubby=y selection")
    trunk = args.tree.resolve() / "trunk"
    assets = Path(__file__).resolve().parent
    ca_bundle = (assets / "cacert-2026-09-25.pem").read_bytes()
    if hashlib.sha256(ca_bundle).hexdigest() != "a41b5d356aea97a529fe27e0f7316d2f9d946d75927476cf9cf1b90637d00505":
        raise RuntimeError("Pinned Stubby CA bundle checksum mismatch")
    edits = {}
    template = trunk / "configs/templates/WR1200JS.config"
    template_text = template.read_text(encoding="utf-8")
    if "CONFIG_FIRMWARE_INCLUDE_STUBBY" in template_text:
        raise RuntimeError("Stubby template selector already exists")
    edits[template] = template_text.rstrip() + "\nCONFIG_FIRMWARE_INCLUDE_STUBBY=n\n"
    for filename, package in [("libs/Makefile", "libyaml"), ("user/Makefile", "stubby")]:
        path = trunk / filename
        edits[path] = register(path.read_text(encoding="utf-8"),
            "dir_$(CONFIG_FIRMWARE_INCLUDE_STUBBY) += " + package,
            " += " + package)
    flags = trunk / "user/shared/cflags.mk"
    flags_text = flags.read_text(encoding="utf-8")
    if "APP_STUBBY" in flags_text:
        raise RuntimeError("APP_STUBBY already present")
    edits[flags] = flags_text + ("\nifeq ($(CONFIG_FIRMWARE_INCLUDE_STUBBY),y)\n"
        "CFLAGS += -DAPP_STUBBY\nendif\n")
    defaults = trunk / "user/shared/defaults.c"
    defaults_text = defaults.read_text(encoding="utf-8")
    schema = json.loads((assets / "nvram-schema.json").read_text(encoding="utf-8"))
    entries = schema["entries"]
    names = [entry["name"] for entry in entries]
    if len(names) != len(set(names)) or len(entries) != 13:
        raise RuntimeError("Unexpected Stubby parameter schema")
    for entry in entries:
        if entry["name"] in defaults_text:
            raise RuntimeError("Existing Stubby parameter requires inspection: " + entry["name"])
    anchor = "struct nvram_pair router_defaults[] = {\n"
    if defaults_text.count(anchor) != 1:
        raise RuntimeError("Expected one router defaults table")
    block = "#if defined(APP_STUBBY)\n" + "".join(
        '\t{ "' + entry["name"] + '", ' + json.dumps(entry["default"]) + ' },\n'
        for entry in entries) + "#endif\n"
    # Only factory defaults are extended. Existing stored values are never rewritten here.
    edits[defaults] = defaults_text.replace(anchor, anchor + block, 1)
    services = trunk / "user/rc/services.c"
    services_text = services.read_text(encoding="utf-8")
    if "stop_stubby" in services_text or "services-stubby.c" in services_text:
        raise RuntimeError("Existing Stubby lifecycle integration requires inspection")
    stop_anchor = "stop_services(int stopall)\n{\n"
    if services_text.count(stop_anchor) != 1:
        raise RuntimeError("Expected one services shutdown anchor")
    services_text = services_text.replace(stop_anchor,
        stop_anchor + "#if defined(APP_STUBBY)\n\tstop_stubby();\n#endif\n", 1)
    edits[services] = services_text + (
        '\n#if defined(APP_STUBBY)\n#include "services-stubby.c"\n#endif\n')
    header = trunk / "user/rc/rc.h"
    header_text = header.read_text(encoding="utf-8")
    if "start_stubby" in header_text:
        raise RuntimeError("Stubby declarations already exist")
    guard_end = header_text.rfind("#endif")
    if guard_end < 0:
        raise RuntimeError("Missing rc header guard")
    declarations = ("\n#if defined(APP_STUBBY)\nint is_stubby_run(void);\n"
        "void stop_stubby(void);\nint start_stubby(void);\n"
        "void restart_stubby(void);\n#endif\n")
    edits[header] = header_text[:guard_end] + declarations + header_text[guard_end:]
    rc = trunk / "user/rc/rc.c"
    rc_text = rc.read_text(encoding="utf-8")
    boot_anchor = "\tstart_services_once(is_ap_mode);\n"
    if "start_stubby" in rc_text or rc_text.count(boot_anchor) != 1:
        raise RuntimeError("Inspect Stubby startup anchor")
    rc_text = rc_text.replace(boot_anchor, boot_anchor +
        '#if defined(APP_STUBBY)\n\tif (start_stubby() != 0)\n'
        '\t\tlogmessage("Stubby", "Startup failed");\n#endif\n', 1)
    dispatch_anchor = '#if defined(APP_IPERF3)\n\t\telse if (strcmp(entry->d_name, RCN_RESTART_IPERF3) == 0)'
    if rc_text.count(dispatch_anchor) != 1:
        raise RuntimeError("Expected one rc notification dispatch anchor")
    edits[rc] = rc_text.replace(dispatch_anchor,
        '#if defined(APP_STUBBY)\n\t\telse if (strcmp(entry->d_name, "restart_stubby") == 0)\n'
        '\t\t{\n\t\t\trestart_stubby();\n\t\t}\n#endif\n' + dispatch_anchor, 1)
    dns = trunk / "user/rc/services_ex.c"
    dns_text = dns.read_text(encoding="utf-8")
    include_anchor = "int\nstart_dns_dhcpd(int is_ap_mode)"
    dns_anchor = '\t\tfprintf(fp, "listen-address=%s\\n", ipaddr);\n'
    if "dnsmasq-stubby.c" in dns_text or dns_text.count(include_anchor) != 1 or dns_text.count(dns_anchor) != 1:
        raise RuntimeError("Inspect dnsmasq Stubby integration anchors")
    dns_text = dns_text.replace(include_anchor,
        '#if defined(APP_STUBBY)\n#include "dnsmasq-stubby.c"\n#endif\n\n' + include_anchor, 1)
    edits[dns] = dns_text.replace(dns_anchor, dns_anchor +
        '#if defined(APP_STUBBY)\n\t\tstubby_dnsmasq_config(fp);\n#endif\n', 1)
    common = trunk / "user/httpd/common.h"
    common_text = common.read_text(encoding="utf-8")
    bits = [int(bit) for bit in re.findall(r"^#define\s+EVM_\w+\s+\(1ULL\s*<<\s*(\d+)\)", common_text, re.M)]
    if len(bits) != len(set(bits)) or any(bit >= 64 for bit in bits) or 56 in bits:
        raise RuntimeError("Repair/inspect HTTP event masks before Stubby integration")
    if "EVM_RESTART_STUBBY" in common_text:
        raise RuntimeError("Stubby event already defined")
    # Match the actual final header guard without assuming its spelling.
    guard_end = common_text.rfind("#endif")
    if guard_end < 0:
        raise RuntimeError("Missing HTTP header guard")
    edits[common] = common_text[:guard_end] + (
        "\n#define EVM_RESTART_STUBBY (1ULL << 56)\n"
        "#define EVT_RESTART_STUBBY 2\n\n") + common_text[guard_end:]
    variables = trunk / "user/httpd/variables.c"
    variable_text = variables.read_text(encoding="utf-8")
    variable_anchor = "\tstruct variable variables_LANHostConfig[] = {\n"
    event_anchor = '\t\t{EVM_RESTART_IPERF3,\tEVT_RESTART_IPERF3,\t\tRCN_RESTART_IPERF3,\t0},\n'
    if "stubby_enable" in variable_text or variable_text.count(variable_anchor) != 1 or variable_text.count(event_anchor) != 1:
        raise RuntimeError("Inspect Stubby HTTP registration anchors")
    fields = "#if defined(APP_STUBBY)\n"
    for name in names:
        event = "EVM_RESTART_STUBBY|EVM_RESTART_DHCPD|EVM_BLOCK_UNSAFE"
        fields += '\t\t\t{"' + name + '", "", NULL, ' + event + '},\n'
    fields += "#endif\n"
    variable_text = variable_text.replace(variable_anchor, variable_anchor + fields, 1)
    edits[variables] = variable_text.replace(event_anchor, event_anchor +
        '#if defined(APP_STUBBY)\n\t\t{EVM_RESTART_STUBBY, EVT_RESTART_STUBBY, "restart_stubby", 0},\n#endif\n', 1)
    web = trunk / "user/httpd/web_ex.c"
    web_text = web.read_text(encoding="utf-8")
    if "found_app_stubby" in web_text:
        raise RuntimeError("Stubby capability already exists")
    start = web_text.index("ej_firmware_caps_hook(")
    end = web_text.index("\nstatic ", start)
    segment = web_text[start:end]
    anchor = "\treturn 0;\n}"
    if segment.count(anchor) != 1:
        raise RuntimeError("Inspect capability function return anchor")
    segment = segment.replace(anchor,
        '#if defined(APP_STUBBY)\n\twebsWrite(wp, "function found_app_stubby() { return 1; }\\n");\n'
        '#else\n\twebsWrite(wp, "function found_app_stubby() { return 0; }\\n");\n#endif\n' + anchor, 1)
    edits[web] = web_text[:start] + segment + web_text[end:]
    www = trunk / "user/www/Makefile"
    www_text = www.read_text(encoding="utf-8")
    if "Advanced_Services_DoT.asp" in www_text or www_text.count("clean:\n") != 1:
        raise RuntimeError("Inspect www packaging anchors")
    edits[www] = www_text.replace("clean:\n",
        'ifneq ($(CONFIG_FIRMWARE_INCLUDE_STUBBY),y)\n'
        '\trm -f $(INSTALLDIR)/www/Advanced_Services_DoT.asp\nendif\nclean:\n', 1)
    footer = trunk / "user/www/dict/EN.footer"
    footer_text = footer.read_text(encoding="utf-8")
    existing_keys = {line.split("=", 1)[0] for line in footer_text.splitlines() if "=" in line}
    additions = [line for line in (assets / "EN-stubby.footer").read_text(encoding="utf-8").splitlines()
                 if line.split("=", 1)[0] not in existing_keys]
    edits[footer] = footer_text.rstrip() + "\n" + "\n".join(additions) + "\n"
    services_page = trunk / "user/www/n56u_ribbon_fixed/Advanced_Services_Content.asp"
    page_text = services_page.read_text(encoding="utf-8")
    menu_anchor = "\tload_body();\n"
    form_anchor = '<form method="post"'
    if "stubby_settings_link" in page_text or page_text.count(menu_anchor) != 1 or page_text.count(form_anchor) != 1:
        raise RuntimeError("Inspect services-page menu anchors")
    page_text = page_text.replace(menu_anchor, menu_anchor +
        "\tshowhide_div('stubby_settings_link', found_app_stubby());\n", 1)
    edits[services_page] = page_text.replace(form_anchor,
        '<div id="stubby_settings_link" style="display:none; margin:10px">'
        '<a href="Advanced_Services_DoT.asp"><#Services_Menu_4#> (Stubby)</a></div>\n' + form_anchor, 1)
    busybox = trunk / "configs/boards/busybox.config"
    bb_text = busybox.read_text(encoding="utf-8")
    for option in ["FLOCK", "PIDOF", "AWK", "ASH"]:
        if "CONFIG_" + option + "=y\n" not in bb_text:
            raise RuntimeError("Required BusyBox option missing: " + option)
    anchor = "# CONFIG_MKTEMP is not set"
    if bb_text.count(anchor) != 1:
        raise RuntimeError("Inspect existing MKTEMP setting before integration")
    # This script is invoked only when Stubby is selected; other builds are unchanged.
    edits[busybox] = bb_text.replace(anchor, "CONFIG_MKTEMP=y", 1)
    copies = [
        (assets / "libyaml/Makefile", trunk / "libs/libyaml/Makefile"),
        (assets / "Makefile", trunk / "user/stubby/Makefile"),
        (assets / "stubby.sh", trunk / "user/stubby/stubby.sh"),
        (assets / "dot.json", trunk / "user/stubby/dot.json"),
        (assets / "cacert-2026-09-25.pem", trunk / "user/stubby/cacert-2026-09-25.pem"),
        (assets / "services-stubby.c", trunk / "user/rc/services-stubby.c"),
        (assets / "dnsmasq-stubby.c", trunk / "user/rc/dnsmasq-stubby.c"),
        (assets / "Advanced_Services_DoT.asp", trunk / "user/www/n56u_ribbon_fixed/Advanced_Services_DoT.asp"),
    ]
    for source, destination in copies:
        if not source.is_file() or destination.exists():
            raise RuntimeError("Missing asset or existing destination: " + str(destination))
    # Validate everything above before mutating the prepared source tree.
    for destination, text in edits.items():
        destination.write_text(text, encoding="utf-8")
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    print("Stubby build registration applied; runtime/backend/UI still required")


if __name__ == "__main__":
    main()
