#!/usr/bin/env python3
"""Add read-only USB/IP runtime observation to the existing USB page."""
import argparse
import re
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("--config", type=Path, required=True)
args = parser.parse_args()
if "CONFIG_FIRMWARE_INCLUDE_USBIP=y" not in args.config.read_text(encoding="utf-8").splitlines():
    print("USB/IP not selected; no endpoint or panel added")
    raise SystemExit(0)
root = args.source / "trunk/user"

web_ex = root / "httpd/web_ex.c"
source = web_ex.read_text(encoding="utf-8")
handler_anchor = "struct ej_handler ej_handlers[] =\n"
handler_entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if source.count(handler_anchor) != 1 or source.count(handler_entry) != 1:
    raise SystemExit("USB/IP status HTTP anchors changed")
if "ej_wr_usbip_state" in source:
    raise SystemExit("USB/IP status endpoint already present")

endpoint = r'''
/* Observation only. Module/process presence does not prove USB/IP connectivity. */
static int wr_usbip_path_state(const char *path)
{
 struct stat st;
 /* An unavailable sysfs mount is unknown, not evidence of an unloaded module. */
 if (stat("/sys/module", &st) != 0 || !S_ISDIR(st.st_mode) ||
     access("/sys/module", R_OK | X_OK) != 0) return 2;
 if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 1 : 2;
 return (errno == ENOENT || errno == ENOTDIR) ? 0 : 2;
}

static int ej_wr_usbip_state(int eid, webs_t wp, int argc, char **argv)
{
 int daemon_state;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "{\"error\":\"invalid_request\"}");
 daemon_state = access("/proc/self/stat", R_OK) ? 2 : (pids("usbipd") > 0 ? 1 : 0);
 return websWrite(wp,
  "{\"core\":%d,\"host\":%d,\"vhci\":%d,\"daemon\":%d}",
  wr_usbip_path_state("/sys/module/usbip_core"),
  wr_usbip_path_state("/sys/module/usbip_host"),
  wr_usbip_path_state("/sys/module/vhci_hcd"), daemon_state);
}
'''
source = source.replace(handler_anchor, endpoint + "\n" + handler_anchor)
source = source.replace(
    handler_entry,
    handler_entry + '\t{ "wr_usbip_state", ej_wr_usbip_state},\n',
)

page = root / "www/n56u_ribbon_fixed/Advanced_Printer_others.asp"
html = page.read_text(encoding="utf-8")
initial_pattern = r"function initial\(\)\s*\{"
if len(re.findall(initial_pattern, html)) != 1:
    raise SystemExit("USB/IP status page initial() anchor changed")
apply_row = '''                                        <tr>
                                            <td colspan="2">
                                                <center><input class="btn btn-primary"'''
if html.count(apply_row) != 1 or "wr_usbip_status" in html:
    raise SystemExit("USB/IP status page table anchor changed")

javascript = r'''
var wrUSBIPBusy = false;
var wrUSBIPLabels = {
 loaded: "<#WRUSBIPLoaded#>", absent: "<#WRUSBIPNotLoaded#>",
 running: "<#WRUSBIPRunning#>", stopped: "<#WRUSBIPStopped#>",
 unknown: "<#WRUSBIPUnknown#>"
};
function wrUSBIPValue(value, process) {
 if (value === 1) return process ? wrUSBIPLabels.running : wrUSBIPLabels.loaded;
 if (value === 0) return process ? wrUSBIPLabels.stopped : wrUSBIPLabels.absent;
 return wrUSBIPLabels.unknown;
}
function wrUSBIPRender(value) {
 var valid = value && typeof value === "object";
 ["core", "host", "vhci", "daemon"].forEach(function(key) {
  valid = valid && typeof value[key] === "number" && isFinite(value[key]) &&
          Math.floor(value[key]) === value[key] && value[key] >= 0 && value[key] <= 2;
 });
 if (!valid) value = {core:2, host:2, vhci:2, daemon:2};
 $j("#wr_usbip_core").text(wrUSBIPValue(value.core, false));
 $j("#wr_usbip_host").text(wrUSBIPValue(value.host, false));
 $j("#wr_usbip_vhci").text(wrUSBIPValue(value.vhci, false));
 $j("#wr_usbip_daemon").text(wrUSBIPValue(value.daemon, true));
}
function wrUSBIPRefresh() {
 if (wrUSBIPBusy || document.hidden) return;
 wrUSBIPBusy = true;
 /* Previous observations are not evidence about the pending request. */
 wrUSBIPRender(null);
 $j.ajax({url:"/update.cgi", data:{output:"wr_usbip_state"}, dataType:"json", cache:false, timeout:5000})
  .done(function(value) { wrUSBIPRender(value); })
  .fail(function() { wrUSBIPRender(null); })
  .always(function() { wrUSBIPBusy = false; });
}
'''
html = html.replace("function initial(){", javascript + "\nfunction initial(){")
initial = '''function initial(){
	var id_menu = 5;'''
replacement = '''function initial(){
	wrUSBIPRender(<% wr_usbip_state(); %>);
	window.setInterval(wrUSBIPRefresh, 30000);
	var id_menu = 5;'''
if html.count(initial) != 1:
    raise SystemExit("USB/IP status page initial body changed")
html = html.replace(initial, replacement)

panel = '''                                        <tr>
                                            <th colspan="2"><#WRUSBIPTitle#></th>
                                        </tr>
                                        <tr><th><#WRUSBIPCore#></th><td id="wr_usbip_core"><#WRUSBIPUnknown#></td></tr>
                                        <tr><th><#WRUSBIPHost#></th><td id="wr_usbip_host"><#WRUSBIPUnknown#></td></tr>
                                        <tr><th><#WRUSBIPVHCI#></th><td id="wr_usbip_vhci"><#WRUSBIPUnknown#></td></tr>
                                        <tr><th><#WRUSBIPDaemon#></th><td id="wr_usbip_daemon"><#WRUSBIPUnknown#></td></tr>
                                        <tr>
                                            <td colspan="2">
                                                <p class="help-block"><#WRUSBIPNote#></p>
                                                <button type="button" class="btn" onclick="wrUSBIPRefresh()"><#WRUSBIPRefresh#></button>
                                            </td>
                                        </tr>
'''
html = html.replace(apply_row, panel + apply_row)

labels = {
    "EN.footer": [
        "USB/IP runtime status", "USB/IP core module", "USB/IP export module",
        "USB/IP client module", "usbipd process", "Loaded", "Not loaded",
        "Running", "Stopped", "Unknown", "Refresh status",
        "Read-only module and process observation. Connectivity, exported devices and access control are not verified. The daemon remains stopped by default.",
    ],
    "UK.dict": [
        "Стан USB/IP", "Основний модуль USB/IP", "Модуль експорту USB/IP",
        "Клієнтський модуль USB/IP", "Процес usbipd", "Завантажено", "Не завантажено",
        "Запущено", "Зупинено", "Невідомо", "Оновити стан",
        "Лише читання стану модулів і процесу. З’єднання, експортовані пристрої та контроль доступу не перевіряються. Демон за замовчуванням зупинений.",
    ],
    "RU.dict": [
        "Состояние USB/IP", "Основной модуль USB/IP", "Модуль экспорта USB/IP",
        "Клиентский модуль USB/IP", "Процесс usbipd", "Загружен", "Не загружен",
        "Запущен", "Остановлен", "Неизвестно", "Обновить состояние",
        "Только чтение состояния модулей и процесса. Соединение, экспортированные устройства и контроль доступа не проверяются. Демон по умолчанию остановлен.",
    ],
}
keys = ["Title", "Core", "Host", "VHCI", "Daemon", "Loaded", "NotLoaded",
        "Running", "Stopped", "Unknown", "Refresh", "Note"]
changes = [(web_ex, source), (page, html)]
for filename, values in labels.items():
    path = root / "www/dict" / filename
    content = path.read_text(encoding="utf-8")
    if "WRUSBIPTitle=" in content:
        raise SystemExit("USB/IP status labels already present")
    content = content.rstrip("\n") + "\n" + "\n".join(
        "WRUSBIP" + key + "=" + value for key, value in zip(keys, values)
    ) + "\n"
    changes.append((path, content))

for path, content in changes:
    path.write_text(content, encoding="utf-8")
print("Prepared read-only USB/IP module and daemon status")
