#!/usr/bin/env python3
"""Port WPAD presentation/storage without automatically advertising a proxy."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("tree", type=Path)
args = parser.parse_args()
root = args.tree / "trunk"
edits = {}
template = root / "configs/templates/WR1200JS.config"
template_text = template.read_text(encoding="utf-8")
if "CONFIG_FIRMWARE_INCLUDE_WPAD" in template_text:
    raise RuntimeError("WPAD template selector already exists")
edits[template] = template_text + '\n# Optional WPAD/PAC support; no automatic proxy advertisement.\nCONFIG_FIRMWARE_INCLUDE_WPAD=n\n'


def change(path, anchor, addition):
    target = root / path
    text = edits.get(target, target.read_text(encoding="utf-8"))
    if text.count(anchor) != 1:
        raise RuntimeError("Unexpected anchor in " + path)
    edits[target] = text.replace(anchor, addition + anchor, 1)


flags = root / "user/shared/cflags.mk"
text = flags.read_text(encoding="utf-8")
if "SUPPORT_WPAD" in text:
    raise RuntimeError("WPAD already present; inspect before applying")
edits[flags] = text + '\nifeq ($(CONFIG_FIRMWARE_INCLUDE_WPAD),y)\nCFLAGS += -DSUPPORT_WPAD\nendif\n'
change("user/www/Makefile", "ifeq ($(CONFIG_FIRMWARE_INCLUDE_LANG_BR),y)",
       'ifeq ($(CONFIG_FIRMWARE_INCLUDE_WPAD),y)\n'
       '\tln -sf /etc/storage/wpad.dat $(ROMFS_DIR)/www/wpad.dat\n'
       '\tln -sf /etc/storage/wpad.dat $(ROMFS_DIR)/www/wpad.da\n'
       '\tln -sf /etc/storage/wpad.dat $(ROMFS_DIR)/www/proxy.pac\nendif\n')
change("user/httpd/web_ex.c", '\t/* cached javascript files w/o translations */',
       '#if defined(SUPPORT_WPAD)\n'
       '\t{ "wpad.dat", "application/x-ns-proxy-autoconfig", no_cache_IE, NULL, do_file, 0 },\n'
       '\t{ "wpad.da", "application/x-ns-proxy-autoconfig", no_cache_IE, NULL, do_file, 0 },\n'
       '\t{ "proxy.pac", "application/x-ns-proxy-autoconfig", no_cache_IE, NULL, do_file, 0 },\n#endif\n')
cap = 'ej_firmware_caps_hook(int eid, webs_t wp, int argc, char **argv) \n{\n'
target = root / "user/httpd/web_ex.c"
text = edits[target]
if text.count(cap) != 1:
    raise RuntimeError("Capability hook changed")
edits[target] = text.replace(cap, cap +
    '#if defined(SUPPORT_WPAD)\n'
    '\tfprintf(wp, "function found_support_wpad() { return 1; }\\n");\n'
    '#else\n\tfprintf(wp, "function found_support_wpad() { return 0; }\\n");\n#endif\n', 1)
change("user/httpd/variables.c", '\t\t\t{"dhcp_enable_x",',
       '#if defined(SUPPORT_WPAD)\n'
       '\t\t\t{"scripts.wpad.dat", "File", NULL, EVM_BLOCK_UNSAFE},\n#endif\n')
change("user/httpd/web_ex.c", '\t\t\t} else if (!strncmp(v->name, "scripts.", 8)) {',
       '#if defined(SUPPORT_WPAD)\n'
       '\t\t\t} else if (!strcmp(v->name, "scripts.wpad.dat")) {\n'
       '\t\t\t\tif (write_textarea_to_file(value, STORAGE_SCRIPTS_DIR, "wpad.dat"))\n'
       '\t\t\t\t\tdoSystem("/sbin/mtd_storage.sh save");\n'
       '#endif\n')
change("user/scripts/mtd_storage.sh", '\t# create user dnsmasq.conf',
       '\t# Initialize only an absent PAC file; existing user configuration is preserved.\n'
       '\tif [ -L /www/wpad.dat ] && [ ! -e "$dir_storage/wpad.dat" ] && [ ! -L "$dir_storage/wpad.dat" ]; then\n'
       '\t\tprintf \'function FindProxyForURL(url, host) { return "DIRECT"; }\\n\' > "$dir_storage/wpad.dat"\n'
       '\t\tchmod 644 "$dir_storage/wpad.dat"\n\tfi\n\n')
change("user/www/n56u_ribbon_fixed/Advanced_DHCP_Content.asp", "\tshow_footer();",
       "\tshowhide_div('row_wpad', found_support_wpad() && !get_ap_mode());\n"
       "\tinputCtrl(document.form['scripts.wpad.dat'], login_safe());\n")
change("user/www/n56u_ribbon_fixed/Advanced_DHCP_Content.asp", '                                        <tr id="row_dservers">',
       '                                        <tr id="row_wpad" style="display:none">\n'
       '                                            <td colspan="2">WPAD / PAC (wpad.dat)\n'
       '                                                <textarea rows="16" wrap="off" spellcheck="false" maxlength="65536" class="span12" name="scripts.wpad.dat"><% nvram_dump("scripts.wpad.dat",""); %></textarea>\n'
       '                                            </td>\n                                        </tr>\n')
# All anchors are validated before any writes. Selector registration is separate.
for target, text in edits.items():
    target.write_text(text, encoding="utf-8")
print("WPAD code applied; no DHCP/DNS proxy advertisement added")
