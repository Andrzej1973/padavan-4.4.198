#!/usr/bin/env python3
"""Add the read-only stored-profile table to the VPN client page."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tree", type=Path, help="Padavan tree root")
args = parser.parse_args()
here = Path(__file__).resolve().parent

httpd = args.tree / "trunk/user/httpd"
web = httpd / "web_ex.c"
page = args.tree / "trunk/user/www/n56u_ribbon_fixed/vpncli.asp"
text = web.read_text(encoding="utf-8")
html = page.read_text(encoding="utf-8")

if "wr_vpn_profile_rows" in text:
    raise RuntimeError("VPN profile rows already integrated")

# The injected code includes this header from the httpd directory.
(httpd / "vpn-profiles-render.h").write_text(
    (here / "web/vpn-profiles-render.h").read_text(encoding="utf-8"),
    encoding="utf-8", newline="\n")
(httpd / "vpn-create-request.h").write_bytes((here / "web/vpn-create-request.h").read_bytes())
(httpd / "vpn-edit-request.h").write_bytes((here / "web/vpn-edit-request.h").read_bytes())

mime_anchor = "struct mime_handler mime_handlers[] = {"
if text.count(mime_anchor) != 1:
    raise RuntimeError("mime_handlers anchor changed")
injection = ((here / "web/vpn-profiles.inc").read_text(encoding="utf-8") + "\n" +
             (here / "web/vpn-profiles-action.inc").read_text(encoding="utf-8") + "\n" +
             (here / "web/vpn-profiles-export.inc").read_text(encoding="utf-8") + "\n")
injection += (here / "web/vpn-profiles-create.inc").read_text(encoding="utf-8") + "\n"
injection += (here / "web/vpn-profiles-edit.inc").read_text(encoding="utf-8") + "\n"
injection += (here / "web/vpn-profiles-observe.inc").read_text(encoding="utf-8") + "\n"
text = text.replace(mime_anchor, injection + mime_anchor, 1)

ej_anchor = "struct ej_handler ej_handlers[] =\n{\n"
if text.count(ej_anchor) != 1:
    raise RuntimeError("ej_handlers anchor changed")
entries = ('\t{ "wr_vpn_profile_rows", ej_wr_vpn_profile_rows},\n'
           '\t{ "wr_vpn_token", ej_wr_vpn_token},\n'
           '\t{ "wr_vpn_action_state", ej_wr_vpn_action_state},\n')
entries += '\t{ "wr_vpn_profile_observation", ej_wr_vpn_profile_observation},\n'
text = text.replace(ej_anchor, ej_anchor + entries, 1)

route_anchor = '\t{ "update.cgi*",'
if text.count(route_anchor) != 1:
    raise RuntimeError("update.cgi route anchor changed")
route = ('\t{ "wr_vpn_action.cgi*", "application/json", no_cache_IE,\n'
         '\t  wr_vpn_action_input, wr_vpn_action_output, 1 },\n')
route += ('\t{ "wr_vpn_export.cgi*", "application/json", no_cache_IE,\n'
          '\t  wr_vpn_export_input, wr_vpn_export_output, 1 },\n')
route += ('\t{ "wr_vpn_create.cgi*", "application/json", no_cache_IE,\n'
          '\t  wr_vpn_create_input, wr_vpn_create_output, 1 },\n')
route += ('\t{ "wr_vpn_edit.cgi*", "application/json", no_cache_IE,\n'
          '\t  wr_vpn_edit_input, wr_vpn_edit_output, 1 },\n')
text = text.replace(route_anchor, route + route_anchor, 1)

main_path = httpd / "httpd.c"
main = main_path.read_text(encoding="utf-8")
method_anchor = "\tquery = file;"
if main.count(method_anchor) != 1 or "wr_vpn_request_is_post" in main:
    raise RuntimeError("httpd method anchor changed")
main = main.replace(method_anchor,
                    "\twr_vpn_method_post = (method_id == HTTP_METHOD_POST);\n" + method_anchor, 1)
include_anchor = "#include <stdio.h>"
if main.count(include_anchor) != 1:
    raise RuntimeError("httpd include anchor changed")
main = main.replace(include_anchor,
                    include_anchor + "\nstatic int wr_vpn_method_post;\n"
                    "int wr_vpn_request_is_post(void) { return wr_vpn_method_post; }\n", 1)
main_path.write_text(main, encoding="utf-8", newline="\n")

footer_anchor = "    </form>"
if html.count(footer_anchor) != 1:
    raise RuntimeError("vpncli form anchor changed")
section = (here / "web/vpn-profiles-page.html").read_text(encoding="utf-8")
html = html.replace(footer_anchor, section + "\n" + footer_anchor, 1)

texts = {
    "EN.footer": (
        ("WRVPN_PROFILES_TITLE", "Stored VPN profiles"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Name"),
        ("WRVPN_REVISION", "Revision"),
    ),
    "UK.dict": (
        ("WRVPN_PROFILES_TITLE", "Збережені VPN-профілі"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Назва"),
        ("WRVPN_REVISION", "Ревізія"),
    ),
    "RU.dict": (
        ("WRVPN_PROFILES_TITLE", "Сохранённые VPN-профили"),
        ("WRVPN_ID", "ID"),
        ("WRVPN_NAME", "Название"),
        ("WRVPN_REVISION", "Ревизия"),
    ),
}
create_texts = {
    "WRVPN_PREVIOUS": ("Previous", "Попередні", "Предыдущие"),
    "WRVPN_NEXT": ("Next", "Наступні", "Следующие"),
    "WRVPN_START": ("Start", "Запустити", "Запустить"),
    "WRVPN_STOP": ("Stop", "Зупинити", "Остановить"),
    "WRVPN_DELETE": ("Delete", "Видалити", "Удалить"),
    "WRVPN_DELETE_CONFIRM": ("Delete profile {id}?", "Видалити профіль {id}?", "Удалить профиль {id}?"),
    "WRVPN_REQUEST_FAILED": ("Request not accepted. Refresh the profile state before retrying.", "Запит не прийнято. Перед повтором оновіть стан профілю.", "Запрос не принят. Перед повтором обновите состояние профиля."),
    "WRVPN_QR_FAILED": ("QR export unavailable. Check the saved profile.", "Експорт QR недоступний. Перевірте збережений профіль.", "Экспорт QR недоступен. Проверьте сохранённый профиль."),
    "WRVPN_QR_HIDE": ("Hide QR and configuration", "Приховати QR і конфігурацію", "Скрыть QR и конфигурацию"),
    "WRVPN_PROTECT": ("Protected address subnets", "Захищені підмережі адрес", "Защищённые подсети адресов"),
    "WRVPN_PROTECT_REQUIRED": ("Before starting, enter up to 8 protected CIDR subnets separated by commas, without spaces.", "Перед запуском вкажіть до 8 захищених CIDR-підмереж через кому, без пробілів.", "Перед запуском укажите до 8 защищённых CIDR-подсетей через запятую, без пробелов."),
    "WRVPN_PROTECT_HELP": (
        "Enter actual LAN and existing management-tunnel CIDR subnets, separated by commas, without spaces. Tunnel addresses must not overlap them. This field applies to the next action; it is not saved automatically. It does not prove routing, DNS or management access will remain usable.",
        "Вкажіть фактичні CIDR-підмережі LAN та чинного керівного тунелю через кому, без пробілів. Адреси нового тунелю не мають перетинатися з ними. Поле діє для наступної дії та автоматично не зберігається. Воно не підтверджує коректність маршрутів, DNS чи збереження доступу.",
        "Укажите фактические CIDR-подсети LAN и действующего управляющего туннеля через запятую, без пробелов. Адреса нового туннеля не должны пересекаться с ними. Поле действует для следующего действия и автоматически не сохраняется. Оно не подтверждает корректность маршрутов, DNS или сохранение доступа."),
    "WRVPN_OBSERVE": ("Check link", "Перевірити інтерфейс", "Проверить интерфейс"),
    "WRVPN_LINK_UNKNOWN": ("Link state unknown", "Стан інтерфейсу невідомий", "Состояние интерфейса неизвестно"),
    "WRVPN_LINK_ABSENT": ("Interface absent", "Інтерфейс відсутній", "Интерфейс отсутствует"),
    "WRVPN_LINK_UP": ("Interface UP; VPN connectivity unverified", "Інтерфейс UP; зв’язок VPN не перевірено", "Интерфейс UP; связь VPN не проверена"),
    "WRVPN_LINK_DOWN": ("Interface DOWN", "Інтерфейс DOWN", "Интерфейс DOWN"),
    "WRVPN_PROTOCOL": ("Protocol", "Протокол", "Протокол"),
    "WRVPN_CONFIG": ("Profile configuration", "Конфігурація профілю", "Конфигурация профиля"),
    "WRVPN_CREATE": ("Save new profile", "Зберегти новий профіль", "Сохранить новый профиль"),
    "WRVPN_REFRESH": ("Refresh list", "Оновити список", "Обновить список"),
    "WRVPN_STORAGE_HELP": (
        "Saving a profile here does not confirm storage to flash or automatic startup after reboot. Before restarting, save storage using the router's standard controls and check the result. Keep a private backup of the configuration; it contains keys.",
        "Збереження профілю тут не підтверджує запис у флеш або автоматичний запуск після перезавантаження. Перед перезавантаженням збережіть сховище штатними засобами роутера й перевірте результат. Зберігайте приватну резервну копію конфігурації: вона містить ключі.",
        "Сохранение профиля здесь не подтверждает запись во флеш или автоматический запуск после перезагрузки. Перед перезагрузкой сохраните хранилище штатными средствами роутера и проверьте результат. Храните частную резервную копию конфигурации: она содержит ключи."),
    "WRVPN_CREATE_HELP": (
        "Choose an unused ID and paste a client configuration. For ID 1 this saves WG1 or AWG1 without starting a tunnel. Reload this page to refresh the list.",
        "Оберіть невикористаний ID і вставте клієнтську конфігурацію. Для ID 1 буде збережено WG1 або AWG1 без запуску тунелю. Перезавантажте сторінку для оновлення списку.",
        "Выберите неиспользованный ID и вставьте клиентскую конфигурацию. Для ID 1 будет сохранён WG1 или AWG1 без запуска туннеля. Перезагрузите страницу для обновления списка."),
    "WRVPN_CREATED": ("Profile saved; tunnel not started.", "Профіль збережено; тунель не запущено.", "Профиль сохранён; туннель не запущен."),
    "WRVPN_CREATE_FAILED": (
        "Save unconfirmed. Refresh the list before retrying; check the ID and configuration.",
        "Збереження не підтверджене. Перед повтором оновіть список; перевірте ID та конфігурацію.",
        "Сохранение не подтверждено. Перед повтором обновите список; проверьте ID и конфигурацию."),
}
for language, name in enumerate(("EN.footer", "UK.dict", "RU.dict")):
    texts[name] += tuple((key, values[language]) for key, values in create_texts.items())
for name, entries in texts.items():
    path = args.tree / "trunk/user/www/dict" / name
    existing = path.read_text(encoding="utf-8")
    missing = [f"{key}={value}" for key, value in entries if f"\n{key}=" not in "\n" + existing]
    if missing:
        path.write_text(existing.rstrip("\n") + "\n" + "\n".join(missing) + "\n",
                        encoding="utf-8", newline="\n")

web.write_text(text, encoding="utf-8", newline="\n")
page.write_text(html, encoding="utf-8", newline="\n")
print("PASS added the stored-profile table and action endpoint to the VPN page")
