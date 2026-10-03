#!/usr/bin/env python3
"""Integrate the preserved DoH package into a prepared WR1200JS source tree."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys


def replace(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Inspect DoH integration anchor: ' + old)
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tree', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    selected = [line.strip() for line in args.config.read_text().splitlines()
                if line.strip().startswith('CONFIG_FIRMWARE_INCLUDE_DOH=')]
    if selected != ['CONFIG_FIRMWARE_INCLUDE_DOH=y']:
        raise SystemExit('One explicit DoH=y selection required')
    root = args.tree.resolve()
    trunk = root / 'trunk'
    assets = Path(__file__).resolve().parent
    archive = assets.parents[3] / 'sources/archives/https_dns_proxy-0ba0525.tar.gz'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != 'd3723d0e14612d2d2cab1f64150558a2a9804b54b2108afbb3e08949b4220ba6':
        raise RuntimeError('Preserved DoH source archive mismatch')
    certificate = assets.parent / 'stubby/cacert-2026-09-25.pem'
    if hashlib.sha256(certificate.read_bytes()).hexdigest() != 'a41b5d356aea97a529fe27e0f7316d2f9d946d75927476cf9cf1b90637d00505':
        raise RuntimeError('Pinned CA bundle mismatch')
    busybox = (trunk / 'configs/boards/busybox.config').read_text()
    for key in ('FLOCK', 'PIDOF', 'AWK', 'ASH'):
        if 'CONFIG_' + key + '=y' not in busybox.splitlines():
            raise RuntimeError('DoH lifecycle prerequisite missing: ' + key)
    httpd = trunk / 'user/httpd'
    if 'event_mask_extended' not in (httpd / 'common.h').read_text():
        subprocess.run([sys.executable, str(assets.parent / 'privoxy/extend-event-bank.py'), str(httpd)], check=True)
    schema = json.loads((assets / 'nvram-schema.json').read_text())['entries']
    if len(schema) != 10 or schema.get('doh_enable') != '0':
        raise RuntimeError('Inspect preserved DoH defaults')
    if 'CONFIG_READLINK=y' not in busybox.splitlines():
        busybox = replace(busybox, '# CONFIG_READLINK is not set', 'CONFIG_READLINK=y')
    edits = {trunk / 'configs/boards/busybox.config': busybox}

    def read(relative):
        return (trunk / relative).read_text(encoding='utf-8')

    def set_edit(relative, text):
        edits[trunk / relative] = text

    template = read('configs/templates/WR1200JS.config')
    if 'CONFIG_FIRMWARE_INCLUDE_DOH' in template:
        raise RuntimeError('DoH selector already present')
    set_edit('configs/templates/WR1200JS.config', template.rstrip() + '\nCONFIG_FIRMWARE_INCLUDE_DOH=n\n')
    libs = read('libs/Makefile')
    anchor = 'dir_$(LIBS_INCLUDE_LIBCURL)'
    position = libs.index(anchor)
    libs = libs[:position] + ('ifeq ($(CONFIG_FIRMWARE_INCLUDE_DOH),y)\n'
        'LIBS_INCLUDE_LIBCURL=y\nLIBS_INCLUDE_LIBCARES=y\nLIBS_INCLUDE_LIBEV=y\nendif\n\n') + libs[position:]
    set_edit('libs/Makefile', libs)
    user = read('user/Makefile')
    all_targets = [line for line in user.splitlines(True) if line.startswith('all:')]
    if len(all_targets) != 1 or ' += doh_proxy' in user:
        raise RuntimeError('Inspect DoH package registration')
    set_edit('user/Makefile', user.replace(all_targets[0], 'dir_$(CONFIG_FIRMWARE_INCLUDE_DOH) += doh_proxy\n\n' + all_targets[0], 1))
    flags = read('user/shared/cflags.mk')
    if 'APP_DOH' in flags:
        raise RuntimeError('DoH capability already present')
    set_edit('user/shared/cflags.mk', flags + '\nifeq ($(CONFIG_FIRMWARE_INCLUDE_DOH),y)\nCFLAGS += -DAPP_DOH\nendif\n')
    defaults = read('user/shared/defaults.c')
    for key in schema:
        if '"' + key + '"' in defaults:
            raise RuntimeError('Existing DoH default: ' + key)
    block = '#if defined(APP_DOH)\n' + ''.join('\t{ ' + json.dumps(key) + ', ' + json.dumps(value) + ' },\n' for key, value in schema.items()) + '#endif\n'
    anchor = 'struct nvram_pair router_defaults[] = {\n'
    set_edit('user/shared/defaults.c', replace(defaults, anchor, anchor + block))
    services = read('user/rc/services.c')
    anchor = 'stop_services(int stopall)\n{\n'
    services = replace(services, anchor, anchor + '#if defined(APP_DOH)\n\tstop_doh();\n#endif\n')
    set_edit('user/rc/services.c', services + '\n#if defined(APP_DOH)\n#include "services-doh.c"\n#endif\n')
    header = read('user/rc/rc.h')
    pos = header.rfind('#endif')
    if pos < 0 or 'start_doh' in header:
        raise RuntimeError('Inspect DoH rc declarations')
    set_edit('user/rc/rc.h', header[:pos] + '\n#if defined(APP_DOH)\nint is_doh_run(void);\nvoid stop_doh(void);\nint start_doh(void);\nvoid restart_doh(void);\n#endif\n' + header[pos:])
    rc = read('user/rc/rc.c')
    anchor = '\tstart_services_once(is_ap_mode);\n'
    rc = replace(rc, anchor, anchor + '#if defined(APP_DOH)\n\tif (start_doh() != 0)\n\t\tlogmessage("DoH", "Startup failed");\n#endif\n')
    anchor = '#if defined(APP_IPERF3)\n\t\telse if (strcmp(entry->d_name, RCN_RESTART_IPERF3) == 0)'
    rc = replace(rc, anchor, '#if defined(APP_DOH)\n\t\telse if (strcmp(entry->d_name, "restart_doh") == 0)\n\t\t{\n\t\t\trestart_doh();\n\t\t}\n#endif\n' + anchor)
    set_edit('user/rc/rc.c', rc)
    watchdog = read('user/rc/watchdog.c')
    anchor = '\t\tnvram_set_int("ntp_ready", 1);\n'
    watchdog = replace(watchdog, anchor, anchor + '#if defined(APP_DOH)\n\t\tif (!get_ap_mode() && nvram_match("doh_enable", "1"))\n\t\t\tnotify_rc("restart_doh");\n#endif\n')
    set_edit('user/rc/watchdog.c', watchdog)
    dns = read('user/rc/services_ex.c')
    anchor = 'int\nstart_dns_dhcpd(int is_ap_mode)'
    dns = replace(dns, anchor, '#if defined(APP_DOH)\n#include "dnsmasq-doh.c"\n#endif\n\n' + anchor)
    anchor = '\t\tfprintf(fp, "listen-address=%s\\n", ipaddr);\n'
    dns = replace(dns, anchor, anchor + '#if defined(APP_DOH)\n\t\tdoh_dnsmasq_config(fp);\n#endif\n')
    set_edit('user/rc/services_ex.c', dns)
    common = read('user/httpd/common.h')
    if 'EVMX_RESTART_DOH' in common or re.search(r'^#define\s+EVMX_\w+\s+\(1ULL\s*<<\s*1\)', common, re.M):
        raise RuntimeError('Inspect DoH extended event allocation')
    pos = common.rfind('#endif')
    set_edit('user/httpd/common.h', common[:pos] + '\n#define EVMX_RESTART_DOH (1ULL << 1)\n#define EVT_RESTART_DOH 2\n\n' + common[pos:])
    variables = read('user/httpd/variables.c')
    anchor = '\tstruct variable variables_LANHostConfig[] = {\n'
    fields = '#if defined(APP_DOH)\n' + ''.join('\t\t\t{"' + name + '", "", NULL, EVM_RESTART_DHCPD|EVM_BLOCK_UNSAFE, EVMX_RESTART_DOH},\n' for name in schema) + '#endif\n'
    variables = replace(variables, anchor, anchor + fields)
    anchor = '\t\t{EVM_RESTART_FIREWALL,\t\tEVT_RESTART_FIREWALL,\t\tRCN_RESTART_FIREWALL,\t0},'
    variables = replace(variables, anchor, '#if defined(APP_DOH)\n\t\t{0, EVT_RESTART_DOH, "restart_doh", 0, EVMX_RESTART_DOH, 0},\n#endif\n' + anchor)
    set_edit('user/httpd/variables.c', variables)
    web = read('user/httpd/web_ex.c')
    start = web.index('ej_firmware_caps_hook(')
    end = web.index('\nstatic ', start)
    segment = web[start:end]
    anchor = '\treturn 0;\n}'
    segment = replace(segment, anchor, '#if defined(APP_DOH)\n\twebsWrite(wp, "function found_app_doh() { return 1; }\\n");\n#else\n\twebsWrite(wp, "function found_app_doh() { return 0; }\\n");\n#endif\n' + anchor)
    web = web[:start] + segment + web[end:]
    helper = (assets / 'web-values.c').read_text()
    anchor = 'static u64 restart_needed_bits = 0;'
    web = replace(web, anchor, helper + '\n' + anchor)
    anchor = '{ "nvram_char_to_ascii", ej_nvram_char_to_ascii},'
    web = replace(web, anchor, '#if defined(APP_DOH)\n\t{ "doh_value", ej_doh_value },\n#endif\n\t' + anchor)
    set_edit('user/httpd/web_ex.c', web)
    www = read('user/www/Makefile')
    set_edit('user/www/Makefile', replace(www, 'clean:\n', 'ifneq ($(CONFIG_FIRMWARE_INCLUDE_DOH),y)\n\trm -f $(INSTALLDIR)/www/Advanced_Services_DoH.asp\nendif\nclean:\n'))
    menu = read('user/www/n56u_ribbon_fixed/Advanced_Services_Content.asp')
    menu = replace(menu, '\tload_body();\n', '\tload_body();\n\tshowhide_div("doh_settings_link", found_app_doh());\n')
    menu = replace(menu, '<form method="post"', '<div id="doh_settings_link" style="display:none; margin:10px"><a href="Advanced_Services_DoH.asp">DNS-over-HTTPS</a></div>\n<form method="post"')
    set_edit('user/www/n56u_ribbon_fixed/Advanced_Services_Content.asp', menu)
    copies = [(assets / name, trunk / 'user/doh_proxy' / name) for name in ('Makefile', 'doh_proxy.sh', 'doh.json')]
    copies += [(certificate, trunk / 'user/doh_proxy/cacert.pem'),
        (assets / 'services-doh.c', trunk / 'user/rc/services-doh.c'),
        (assets / 'dnsmasq-doh.c', trunk / 'user/rc/dnsmasq-doh.c'),
        (assets / 'Advanced_Services_DoH.asp', trunk / 'user/www/n56u_ribbon_fixed/Advanced_Services_DoH.asp')]
    for source, destination in copies:
        if not source.is_file() or destination.exists():
            raise RuntimeError('Missing DoH asset or existing destination: ' + str(destination))
    for destination, text in edits.items():
        destination.write_text(text, encoding='utf-8')
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    print('DoH package/backend/WebUI integrated; full image and runtime checks remain required')


if __name__ == '__main__':
    main()
