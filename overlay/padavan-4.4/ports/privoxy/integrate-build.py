#!/usr/bin/env python3
"""Register the Privoxy package and its PCRE2 dependency in a prepared tree.

This covers build registration only. Runtime/WebUI integration is separate.
"""
import argparse
from pathlib import Path
import shutil


def insert_once(text, anchor, insertion, marker):
    if marker in text:
        raise RuntimeError("Already integrated or conflicting marker: " + marker)
    if text.count(anchor) != 1:
        raise RuntimeError("Expected exactly one build anchor: " + anchor)
    return text.replace(anchor, insertion + anchor, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path, help="Prepared Padavan checkout root")
    args = parser.parse_args()
    trunk = args.tree.resolve() / "trunk"
    assets = Path(__file__).resolve().parent
    edits = {}
    template = trunk / "configs/templates/WR1200JS.config"
    template_text = template.read_text(encoding="utf-8")
    if "CONFIG_FIRMWARE_INCLUDE_PRIVOXY" in template_text:
        raise RuntimeError("Inspect existing Privoxy template selector")
    edits[template] = template_text.rstrip() + "\nCONFIG_FIRMWARE_INCLUDE_PRIVOXY=n\n"
    libs = trunk / "libs/Makefile"
    edits[libs] = insert_once(
        libs.read_text(encoding="utf-8"), "all: $(patsubst %,%_only,$(dir_y))",
        "dir_$(CONFIG_FIRMWARE_INCLUDE_PRIVOXY) += libpcre2\n\n",
        " += libpcre2")
    user = trunk / "user/Makefile"
    user_text = user.read_text(encoding="utf-8")
    # all prerequisites are expanded when parsed; registration must precede all.
    anchor = next((line for line in user_text.splitlines(True)
                   if line.startswith("all:")), None)
    if anchor is None:
        raise RuntimeError("User all target missing")
    edits[user] = insert_once(user_text, anchor,
        "dir_$(CONFIG_FIRMWARE_INCLUDE_PRIVOXY) += privoxy\n\n", " += privoxy")
    flags = trunk / "user/shared/cflags.mk"
    flags_text = flags.read_text(encoding="utf-8")
    if "APP_PRIVOXY" in flags_text:
        raise RuntimeError("APP_PRIVOXY already exists; inspect integration")
    edits[flags] = flags_text + (
        "\nifeq ($(CONFIG_FIRMWARE_INCLUDE_PRIVOXY),y)\n"
        "CFLAGS += -DAPP_PRIVOXY\nendif\n")

    defaults = trunk / "user/shared/defaults.c"
    text = defaults.read_text(encoding="utf-8")
    text = insert_once(text, "struct nvram_pair router_defaults[] = {\n",
        "", '"privoxy_enable"')
    edits[defaults] = text.replace("struct nvram_pair router_defaults[] = {\n",
        'struct nvram_pair router_defaults[] = {\n#if defined(APP_PRIVOXY)\n'
        '\t{ "privoxy_enable", "0" },\n#endif\n', 1)
    services = trunk / "user/rc/services.c"
    text = services.read_text(encoding="utf-8")
    text = insert_once(text, "stop_services(int stopall)\n{\n", "", "services-privoxy.c")
    text = text.replace("stop_services(int stopall)\n{\n",
        "stop_services(int stopall)\n{\n#if defined(APP_PRIVOXY)\n\tstop_privoxy();\n#endif\n", 1)
    edits[services] = text + '\n#if defined(APP_PRIVOXY)\n#include "services-privoxy.c"\n#endif\n'
    header = trunk / "user/rc/rc.h"
    text = header.read_text(encoding="utf-8")
    if "start_privoxy" in text or text.rfind("#endif") < 0:
        raise RuntimeError("Inspect Privoxy declarations")
    pos = text.rfind("#endif")
    edits[header] = text[:pos] + ("#if defined(APP_PRIVOXY)\nint is_privoxy_run(void);\n"
        "void start_privoxy(void);\nvoid stop_privoxy(void);\nvoid restart_privoxy(void);\n#endif\n") + text[pos:]
    rc = trunk / "user/rc/rc.c"
    text = rc.read_text(encoding="utf-8")
    anchor = "\tstart_services_once(is_ap_mode);\n"
    text = insert_once(text, anchor, "", "start_privoxy")
    text = text.replace(anchor, anchor + "#if defined(APP_PRIVOXY)\n\tstart_privoxy();\n#endif\n", 1)
    anchor = '#if defined(APP_IPERF3)\n\t\telse if (strcmp(entry->d_name, RCN_RESTART_IPERF3) == 0)'
    edits[rc] = insert_once(text, anchor,
        '#if defined(APP_PRIVOXY)\n\t\telse if (strcmp(entry->d_name, "restart_privoxy") == 0)\n'
        '\t\t{\n\t\t\trestart_privoxy();\n\t\t}\n#endif\n', '"restart_privoxy"')

    # Validate every input/destination before changing the checkout.
    copies = [
        (assets / "libpcre2/Makefile", trunk / "libs/libpcre2/Makefile"),
        (assets / "Makefile", trunk / "user/privoxy/Makefile"),
        (assets / "privoxy.sh", trunk / "user/privoxy/privoxy.sh"),
        (assets / "services-privoxy.c", trunk / "user/rc/services-privoxy.c"),
    ]
    for source, destination in copies:
        if not source.is_file():
            raise RuntimeError("Missing candidate asset: " + str(source))
        if destination.exists():
            raise RuntimeError("Package destination already exists: " + str(destination))
    for destination, text in edits.items():
        destination.write_text(text, encoding="utf-8")
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    print("Privoxy/PCRE2 build registration applied; runtime/UI still required")


if __name__ == "__main__":
    main()
