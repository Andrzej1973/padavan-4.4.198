#!/usr/bin/env python3
"""Make the inherited Shadowsocks client process badge truthful."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = args.source / "trunk/user"
page = root / "www/n56u_ribbon_fixed/Shadowsocks.asp"
html = page.read_text(encoding="utf-8")
start = "\t\tfunction fill_ss_status(status_code) {"
end = "\t\tfunction fill_dns2tcp_status(status_code) {"
if html.count(start) != 1 or html.count(end) != 1:
    raise SystemExit("Shadowsocks status function anchors changed")
begin = html.index(start)
finish = html.index(end, begin)
old = html[begin:finish]
if "WRSSProcessUnknown" in old:
    raise SystemExit("Shadowsocks process status already prepared")
if '$("ss_status").innerHTML' not in old or "fill_ss_status(shadowsocks_status());" not in html:
    raise SystemExit("Shadowsocks status function body changed")
new = '''\t\tfunction fill_ss_status(status_code) {
\t\t\tvar valid = typeof status_code === "number" && isFinite(status_code) && Math.floor(status_code) === status_code;
\t\t\tvar active = valid && status_code > 0;
\t\t\tvar stopped = valid && status_code === 0;
\t\t\tvar stext = active ? "<#WRSSProcessPresent#>" :
\t\t\t\t(stopped ? "<#WRSSProcessStopped#>" : "<#WRSSProcessUnknown#>");
\t\t\t$("ss_status").innerHTML = '<span class="label label-' + (active ? 'success' : 'warning') + '">' + stext + '</span>';
\t\t\t$("domestic_ip").innerHTML = '<iframe src="http://ip.3322.net" height="30" scrolling="no" frameborder="0" marginheight="0" marginwidth="0"></iframe>';
\t\t\t$("foreign_ip").innerHTML = '<iframe src="https://ifconfig.me/ip" height="30" scrolling="no" frameborder="0" marginheight="0" marginwidth="0"></iframe>';
\t\t\t$("gg_status").innerHTML = '<span><img alt="无法访问" src="https://www.google.com/favicon.ico?' + new Date().getTime() + '" /></span>';
\t\t}
'''
html = html[:begin] + new + html[finish:]
row = re.compile(r'(?m)^(?P<indent>\t+)</tr>\r?\n(?P=indent)<tr id="row_pdnsd_run">')
matches = list(row.finditer(html))
if len(matches) != 1 or "WRSSProcessNote" in html:
    raise SystemExit("Shadowsocks status row anchor changed")
indent = matches[0].group("indent")
note = (indent + "</tr>\n" + indent +
        '<tr><td colspan="2"><small><#WRSSProcessNote#></small></td></tr>\n' +
        indent + '<tr id="row_pdnsd_run">')
html = row.sub(lambda _: note, html, count=1)

translations = {
    "EN.footer": {
        "WRSSProcessPresent": "Proxy client process present",
        "WRSSProcessStopped": "No proxy client process found",
        "WRSSProcessUnknown": "Proxy client process state unknown",
        "WRSSProcessNote": "Process presence only; upstream reachability, DNS and client traffic are not verified. Reload this page to take a new sample. The saved enable setting is shown separately.",
    },
    "UK.dict": {
        "WRSSProcessPresent": "Процес проксі-клієнта знайдено",
        "WRSSProcessStopped": "Процесу проксі-клієнта не знайдено",
        "WRSSProcessUnknown": "Стан процесу проксі-клієнта невідомий",
        "WRSSProcessNote": "Перевірено лише наявність процесу; доступність сервера, DNS і трафік клієнта не перевірялися. Перезавантажте сторінку, щоб отримати нове спостереження. Збережений перемикач налаштування показано окремо.",
    },
    "RU.dict": {
        "WRSSProcessPresent": "Процесс прокси-клиента найден",
        "WRSSProcessStopped": "Процесс прокси-клиента не найден",
        "WRSSProcessUnknown": "Состояние процесса прокси-клиента неизвестно",
        "WRSSProcessNote": "Проверено только наличие процесса; доступность сервера, DNS и трафик клиента не проверялись. Перезагрузите страницу, чтобы получить новое наблюдение. Сохранённая настройка переключателя показана отдельно.",
    },
}
for filename, values in translations.items():
    path = root / "www/dict" / filename
    text = path.read_text(encoding="utf-8")
    if "WRSSProcessPresent=" in text:
        raise SystemExit(f"Shadowsocks process labels already exist in {filename}")
    text = text.rstrip("\n") + "\n" + "\n".join(
        f"{key}={value}" for key, value in values.items()) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")

page.write_text(html, encoding="utf-8", newline="\n")
print("Prepared truthful Shadowsocks process badge; proxy functionality remains unverified")
