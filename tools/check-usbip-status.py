#!/usr/bin/env python3
"""Regression checks for the USB/IP runtime status integration."""
import subprocess
import sys
import uuid
from pathlib import Path


repo = Path(__file__).resolve().parents[1]
stage = repo / ("usbip-status-check-" + uuid.uuid4().hex)
user = stage / "trunk/user"
(user / "httpd").mkdir(parents=True)
(user / "www/n56u_ribbon_fixed").mkdir(parents=True)
(user / "www/dict").mkdir(parents=True)

try:
    (user / "httpd/web_ex.c").write_text(
        '#include <errno.h>\n#include <sys/stat.h>\n'
        'struct ej_handler ej_handlers[] =\n{\n'
        '\t{ "json_system_status", ej_system_status_hook},\n};\n', encoding="utf-8"
    )
    page = '''<script>function initial(){
\tvar id_menu = 5;
}</script>
<table>
                                        <tr>
                                            <td colspan="2">
                                                <center><input class="btn btn-primary" type="button"></center>
                                            </td>
                                        </tr>
</table>'''
    (user / "www/n56u_ribbon_fixed/Advanced_Printer_others.asp").write_text(page, encoding="utf-8")
    for name in ("EN.footer", "UK.dict", "RU.dict"):
        (user / "www/dict" / name).write_text("Existing=value\n", encoding="utf-8")

    command = [sys.executable, str(repo / "tools/prepare-usbip-status.py"), str(stage)]
    subprocess.run(command, check=True)
    web = (user / "httpd/web_ex.c").read_text(encoding="utf-8")
    assert '"wr_usbip_state", ej_wr_usbip_state' in web
    for marker in ("/sys/module/usbip_core", "/sys/module/usbip_host",
                   "/sys/module/vhci_hcd", 'pids("usbipd")', 'argc != 0'):
        assert marker in web
    rendered = (user / "www/n56u_ribbon_fixed/Advanced_Printer_others.asp").read_text(encoding="utf-8")
    for marker in ("wr_usbip_core", "wr_usbip_host", "wr_usbip_vhci", "wr_usbip_daemon",
                   'output:"wr_usbip_state"', "document.hidden", "timeout:5000",
                   "setInterval(wrUSBIPRefresh, 30000)"):
        assert marker in rendered
    assert "Connectivity, exported devices" in (user / "www/dict/EN.footer").read_text(encoding="utf-8")
    assert "З’єднання, експортовані пристрої" in (user / "www/dict/UK.dict").read_text(encoding="utf-8")
    assert "Соединение, экспортированные устройства" in (user / "www/dict/RU.dict").read_text(encoding="utf-8")
    duplicate = subprocess.run(command, text=True, capture_output=True)
    assert duplicate.returncode != 0 and "already present" in (duplicate.stdout + duplicate.stderr)
finally:
    if stage.exists():
        for path in sorted(stage.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        stage.rmdir()

print("USB/IP status integration checks passed")
