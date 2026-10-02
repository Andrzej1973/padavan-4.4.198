#!/usr/bin/env python3
"""Expose source VPN page capability names without replacing existing hooks."""
from pathlib import Path
import sys
path = Path(sys.argv[1]) / "trunk/user/httpd/web_ex.c"
text = path.read_text()
anchor = '\twebsWrite(wp,\n\t\t"function support_ipv6() { return %d;}\\n"'
if text.count(anchor) != 1 or "function found_app_awg()" in text:
    raise SystemExit("Unexpected HTTPD capability anchor")
addition = '''
#if defined(APP_AMNEZIAWG)
	websWrite(wp, "function found_app_wg() { return 1;}\\n"
		      "function found_app_awg() { return 1;}\\n");
#else
	websWrite(wp, "function found_app_wg() { return found_app_wireguard();}\\n"
		      "function found_app_awg() { return 0;}\\n");
#endif
#if defined(USE_IPSET)
	websWrite(wp, "function found_support_ipset() { return 1;}\\n");
#else
	websWrite(wp, "function found_support_ipset() { return 0;}\\n");
#endif

'''
path.write_text(text.replace(anchor, addition + anchor))
print("Source VPN capability hooks added: WG, AmneziaWG, IPSet")
