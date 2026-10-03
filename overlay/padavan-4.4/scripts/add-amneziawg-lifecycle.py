#!/usr/bin/env python3
"""Connect AmneziaWG to the existing VPN client/server lifecycle."""
from pathlib import Path
import shutil
import sys
trunk = Path(sys.argv[1]) / "trunk"
overlay = Path(__file__).resolve().parent.parent

def edit(relative, old, new):
    path = trunk / relative
    text = path.read_text()
    if text.count(old) != 1:
        raise SystemExit("Unexpected lifecycle anchor: " + relative + " " + old)
    path.write_text(text.replace(old, new))

edit("user/rc/vpn_client.c",
     '\tvpnc_peer = nvram_safe_get("vpnc_peer");',
     '\tvpnc_peer = nvram_safe_get("vpnc_peer");\n'
     '#if defined(APP_AMNEZIAWG)\n'
     '\tif (nvram_get_int("vpnc_type") == 3)\n'
     '\t\tvpnc_peer = nvram_safe_get("vpnc_wg_peer_endpoint");\n#endif')
edit("user/rc/vpn_client.c",
     '\ti_type = nvram_get_int("vpnc_type");\n#if defined(APP_OPENVPN)',
     '\ti_type = nvram_get_int("vpnc_type");\n'
     '#if defined(APP_AMNEZIAWG)\n\tif (i_type == 3)\n'
     '\t\treturn start_wireguard_client();\n#endif\n#if defined(APP_OPENVPN)')
edit("user/rc/vpn_client.c",
     '\tstop_openvpn_client();\n#endif',
     '\tstop_openvpn_client();\n#endif\n#if defined(APP_AMNEZIAWG)\n'
     '\tstop_wireguard_client();\n#endif')
edit("user/rc/vpn_server.c",
     '\ti_type = nvram_get_int("vpns_type");\n#if defined(APP_OPENVPN)\n\tif (i_type == 2)\n\t\treturn start_openvpn_server();',
     '\ti_type = nvram_get_int("vpns_type");\n#if defined(APP_AMNEZIAWG)\n'
     '\tif (i_type == 3)\n\t\treturn start_wireguard_server();\n#endif\n'
     '#if defined(APP_OPENVPN)\n\tif (i_type == 2)\n\t\treturn start_openvpn_server();')
edit("user/rc/vpn_server.c",
     '\tstop_openvpn_server();\n#endif',
     '\tstop_openvpn_server();\n#endif\n#if defined(APP_AMNEZIAWG)\n'
     '\tstop_wireguard_server();\n#endif')
edit("user/rc/vpn_server.c",
     '\ti_type = nvram_get_int("vpns_type");\n#if defined(APP_OPENVPN)\n\tif (i_type == 2)\n\t\trestart_openvpn_server();',
     '\ti_type = nvram_get_int("vpns_type");\n#if defined(APP_AMNEZIAWG)\n'
     '\tif (i_type == 3) {\n\t\trestart_wireguard_server();\n\t\treturn;\n\t}\n#endif\n'
     '#if defined(APP_OPENVPN)\n\tif (i_type == 2)\n\t\trestart_openvpn_server();')
edit("user/rc/Makefile", "OBJS += vpn_server.o vpn_client.o",
     "OBJS += vpn_server.o vpn_client.o\n"
     "ifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)\n"
     "OBJS += vpn_wireguard.o\nendif")
edit("user/rc/Makefile",
     "\tcd $(INSTALLDIR)/sbin && ln -sf rc restart_vpn_client",
     "\tcd $(INSTALLDIR)/sbin && ln -sf rc restart_vpn_client\n"
     "\tcd $(INSTALLDIR)/sbin && ln -sf rc update_resolvconf")
edit("user/rc/rc.c",
     '\telse if (!strcmp(base, "restart_vpn_client")) {',
     '\telse if (!strcmp(base, "update_resolvconf")) {\n'
     '\t\tupdate_resolvconf(0, 0);\n\t}\n'
     '\telse if (!strcmp(base, "restart_vpn_client")) {')
path = trunk / "user/rc/rc.h"
path.write_text(path.read_text() + '\n#if defined(APP_AMNEZIAWG)\n'
    'int start_wireguard_client(void);\nvoid stop_wireguard_client(void);\n'
    'int start_wireguard_server(void);\nvoid stop_wireguard_server(void);\n'
    'void restart_wireguard_server(void);\n'
    'void update_wireguard_client(void);\nvoid watchdog_wireguard_client(void);\n#endif\n')
edit("user/rc/watchdog.c",
     '\tinet_handler(is_ap_mode);',
     '#if defined(APP_AMNEZIAWG)\n\tif (!is_ap_mode)\n'
     '\t\twatchdog_wireguard_client();\n#endif\n\tinet_handler(is_ap_mode);')
edit("user/rc/firewall_ex.c", '\t/* enable IPv4 forward */',
     '#if defined(APP_AMNEZIAWG)\n\tupdate_wireguard_client();\n#endif\n'
     '\t/* enable IPv4 forward */')
shutil.copyfile(overlay / "trunk/user/rc/vpn_wireguard.c",
                trunk / "user/rc/vpn_wireguard.c")
for name in ("wgc.sh", "wgs.sh", "amneziawg.json"):
    shutil.copyfile(overlay / "trunk/user/amneziawg" / name,
                    trunk / "user/amneziawg" / name)
print("AmneziaWG VPN type 3 client/server lifecycle connected")
