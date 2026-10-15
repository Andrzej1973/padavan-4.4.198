#!/usr/bin/env python3
"""Wire USB/IP into the existing authenticated General Apply path."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--config', type=Path, required=True)
a = p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
root = a.source / 'trunk/user'
pending = {}

def insert(name, anchor, addition):
    path = root / name
    text = pending.get(path, path.read_text())
    if text.count(anchor) != 1:
        raise SystemExit('USB/IP Apply anchor changed: ' + name)
    pending[path] = text.replace(anchor, addition + anchor)

# The complete profile uses all 64 event bits, including ZRAM and Stubby.
# Share the existing USB service transaction instead of allocating a collision.
path = root / 'httpd/common.h'
common, count = re.subn(r'(^#define\s+EVT_RESTART_SPOOLER\s+)1$', r'\g<1>25', path.read_text(), flags=re.M)
if count != 1:
    raise SystemExit('USB/IP USB service wait anchor changed')
pending[path] = common
insert('httpd/variables.c', '\t\t\t{"iperf3_enable", "", NULL, EVM_RESTART_IPERF3},',
       '#endif\n#if defined(APP_USBIP)\n'
       '\t\t\t{"usbip_enable", "", NULL, EVM_RESTART_SPOOLER},\n'
       '#endif\n#if defined(APP_IPERF3)\n')
insert('rc/rc.c', '\t\t\trestart_usb_printer_spoolers();',
       '#if defined(APP_USBIP)\n'
       '\t\t\tif (eval("/usr/sbin/wr-usbip", "reconcile") != 0)\n'
       '\t\t\t\tlogmessage("USB/IP", "Apply failed; inspect service state and wr-usbip log");\n'
       '#endif\n')
page = 'www/n56u_ribbon_fixed/Advanced_Printer_others.asp'
insert(page, '                                        <tr><th><#WRUSBIPCore#>',
       '''                                        <tr><th><#WRUSBIPEnable#></th><td>
                                            <select name="usbip_enable">
                                                <option value="0" <% nvram_match_x("General", "usbip_enable", "0", "selected"); %>><#checkbox_No#></option>
                                                <option value="1" <% nvram_match_x("General", "usbip_enable", "1", "selected"); %>><#checkbox_Yes#></option>
                                            </select><p class="help-block"><#WRUSBIPEnableNote#></p>
                                        </td></tr>
''')
for filename, title, note in [
    ('EN.footer', 'Enable USB/IP server', 'Saved request, separate from observed process state. Apply starts or stops the server. USB devices are not exported automatically. LAN clients may access exported devices; no per-user authentication is provided.'),
    ('UK.dict', 'Увімкнути сервер USB/IP', 'Збережене налаштування, окреме від фактичного стану процесу. Застосувати запускає або зупиняє сервер. USB-пристрої автоматично не експортуються. Клієнти LAN можуть отримати доступ до експортованих пристроїв; автентифікації користувачів немає.'),
    ('RU.dict', 'Включить сервер USB/IP', 'Сохранённая настройка, отдельно от фактического состояния процесса. Применить запускает или останавливает сервер. USB-устройства автоматически не экспортируются. Клиенты LAN могут получить доступ к экспортированным устройствам; аутентификации пользователей нет.'),
]:
    path = root / 'www/dict' / filename
    text = path.read_text()
    if 'WRUSBIPEnable=' in text:
        raise SystemExit('USB/IP Apply labels already present')
    pending[path] = text.rstrip('\n') + '\nWRUSBIPEnable=' + title + '\nWRUSBIPEnableNote=' + note + '\n'
for path, text in pending.items():
    path.write_text(text)
print('Prepared USB/IP General Apply event and EN/UK/RU requested-state control')
