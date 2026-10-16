#!/usr/bin/env python3
"""Localize the ZeroTier page (EN/UK/RU) and replace manual reload with a
bounded, visible-tab status refresh.

Chinese captions, list options and help text inherited from the pinned Padavan
page are replaced with dictionary keys; Moon, static routes and the legacy NAT
switch are grouped afterwards by prepare-advanced-controls.py. The status panel
gains an authenticated JSON state endpoint (/update.cgi?output=zerotier_state),
a 30 s refresh that pauses in hidden tabs, freshness text and an explicit retry
control.

This changes source only. Device runtime behaviour is not verified here.
"""
import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify-image', action='store_true')
args = parser.parse_args()

CJK = re.compile(r'[\u3400-\u9fff]')

# key, English, Ukrainian, Russian
LABELS = [
    ('ZT_OfficialSite', 'ZeroTier website', 'Сайт ZeroTier', 'Сайт ZeroTier'),
    ('ZT_IntroLine1',
     'ZeroTier is an open source, cross-platform virtual VPN LAN for simple site-to-site and remote access.',
     'ZeroTier — відкрита кросплатформна віртуальна VPN-мережа для простого з’єднання мереж і віддаленого доступу.',
     'ZeroTier — открытая кроссплатформенная виртуальная VPN-сеть для простого соединения сетей и удалённого доступа.'),
    ('ZT_IntroLine2',
     'Create or manage a network and authorize clients to reach your private network. Newly joined nodes have no access until you authorize them.',
     'Створіть мережу або керуйте нею та авторизуйте клієнтів для доступу до приватної мережі. Нові вузли не мають доступу, доки ви їх не авторизуєте.',
     'Создайте сеть или управляйте ею и авторизуйте клиентов для доступа к частной сети. Новые узлы не имеют доступа, пока вы их не авторизуете.'),
    ('ZT_Refresh', 'Refresh status', 'Оновити стан', 'Обновить состояние'),
    ('ZT_Disabled', 'Disabled', 'Вимкнено', 'Выключено'),
    ('ZT_Enabled', 'Enabled', 'Увімкнено', 'Включено'),
    ('ZT_EnableClient', 'Enable ZeroTier client', 'Увімкнути клієнт ZeroTier', 'Включить клиент ZeroTier'),
    ('ZT_ClientID', 'ZeroTier client ID', 'Ідентифікатор клієнта ZeroTier', 'Идентификатор клиента ZeroTier'),
    ('ZT_AllowNAT', 'Masquerade overlay clients to LAN (legacy)',
     'Маскування клієнтів overlay у LAN (застаріле)',
     'Маскирование клиентов overlay в LAN (устаревшее)'),
    ('ZT_NatHelp',
     'Legacy switch kept for existing configurations. It takes effect only while Allow access to LAN is On: overlay IPv4 source addresses are then masqueraded toward the LAN, as the older firmware did. It never exposes the WAN or other VPNs.',
     'Застарілий перемикач, збережений для наявних налаштувань. Він діє лише тоді, коли ввімкнено «Дозволити доступ до LAN»: IPv4-адреси джерел overlay тоді маскуються до LAN, як у старій прошивці. Він ніколи не відкриває WAN чи інші VPN.',
     'Устаревший переключатель, сохранённый для существующих настроек. Он действует только при включённом «Разрешить доступ к LAN»: IPv4-адреса источников overlay тогда маскируются в LAN, как в старой прошивке. Он никогда не открывает WAN или другие VPN.'),
    ('ZT_AdvancedHeading', 'Advanced settings', 'Додаткові налаштування', 'Дополнительные настройки'),
    ('ZT_AdvancedShow', 'Show advanced settings', 'Показати додаткові налаштування', 'Показать дополнительные настройки'),
    ('ZT_AdvancedHide', 'Hide advanced settings', 'Сховати додаткові налаштування', 'Скрыть дополнительные настройки'),
    ('ZT_AdvancedHelp',
     'Moon server, static routes and the legacy NAT switch. Collapsed so the page stays short; the Apply control remains visible.',
     'Сервер Moon, статичні маршрути та застарілий перемикач NAT. Згорнуто, щоб сторінка була коротшою; кнопка «Застосувати» залишається видимою.',
     'Сервер Moon, статические маршруты и устаревший переключатель NAT. Свёрнуто, чтобы страница была короче; кнопка «Применить» остаётся видимой.'),
    ('ZT_MoonNetworkID', 'ZeroTier Moon network ID', 'Ідентифікатор мережі ZeroTier Moon', 'Идентификатор сети ZeroTier Moon'),
    ('ZT_MoonEnable', 'Enable ZeroTier Moon server', 'Увімкнути сервер ZeroTier Moon', 'Включить сервер ZeroTier Moon'),
    ('ZT_MoonEndpoint', 'ZeroTier Moon server IP or domain name',
     'IP-адреса або доменне ім’я сервера ZeroTier Moon', 'IP-адрес или доменное имя сервера ZeroTier Moon'),
    ('ZT_MoonEndpointHelp',
     'If left blank, the WAN address is used. An IP address is used as-is; a domain name is resolved to its public IP address.',
     'Якщо поле порожнє, використовується адреса WAN. IP-адреса використовується як є; доменне ім’я розпізнається у публічну IP-адресу.',
     'Если поле пустое, используется адрес WAN. IP-адрес используется как есть; доменное имя разрешается в публичный IP-адрес.'),
    ('ZT_MoonID', 'ZeroTier Moon server ID', 'Ідентификатор сервера ZeroTier Moon', 'Идентификатор сервера ZeroTier Moon'),
    ('ZT_MoonIDHelp',
     'Generated automatically after the Moon server starts. Join it from a client with: zerotier-cli orbit &lt;ID&gt; &lt;ID&gt;',
     'Створюється автоматично після запуску сервера Moon. Приєднання з клієнта: zerotier-cli orbit &lt;ID&gt; &lt;ID&gt;',
     'Создаётся автоматически после запуска сервера Moon. Присоединение с клиента: zerotier-cli orbit &lt;ID&gt; &lt;ID&gt;'),
    ('ZT_RoutesHelp',
     'Add the LAN subnets reachable through other ZeroTier members. Keep IP, gateway and the controller route table consistent. Do not add this router’s own LAN subnet.',
     'Додайте підмережі LAN, доступні через інших учасників ZeroTier. Узгоджуйте IP, шлюз і таблицю маршрутів у контролері. Не додавайте власну підмережу цього роутера.',
     'Добавьте подсети LAN, доступные через других участников ZeroTier. Согласуйте IP, шлюз и таблицу маршрутов в контроллере. Не добавляйте собственную подсеть этого роутера.'),
    ('ZT_ColEnable', 'Enabled', 'Увімкнено', 'Включено'),
    ('ZT_ColGateway', 'Gateway', 'Шлюз', 'Шлюз'),
    ('ZT_Yes', 'Yes', 'Так', 'Да'),
    ('ZT_No', 'No', 'Ні', 'Нет'),
    ('ZT_StatusHeading', 'Node and network status', 'Стан вузла й мережі', 'Состояние узла и сети'),
    ('ZT_StatusHelp',
     'The background monitor refreshes this from the ZeroTier service every 10 seconds. Automatic refresh runs only while this tab is visible; use the button to refresh immediately.',
     'Фоновий монітор оновлює ці дані зі служби ZeroTier кожні 10 секунд. Автоматичне оновлення працює лише коли вкладка видима; кнопка оновлює негайно.',
     'Фоновый монитор обновляет эти данные из службы ZeroTier каждые 10 секунд. Автообновление работает только когда вкладка видима; кнопка обновляет немедленно.'),
    ('ZT_RouterAccess', 'Allow access to this router', 'Дозволити доступ до цього роутера', 'Разрешить доступ к этому роутеру'),
    ('ZT_RouterAccessHelp',
     'Allow ZeroTier members to reach router services, including its web interface and SSH.',
     'Дозволити учасникам ZeroTier доступ до служб роутера, зокрема веб-інтерфейсу та SSH.',
     'Разрешить участникам ZeroTier доступ к службам роутера, включая веб-интерфейс и SSH.'),
    ('ZT_LanAccess', 'Allow access to LAN', 'Дозволити доступ до LAN', 'Разрешить доступ к LAN'),
    ('ZT_LanAccessHelp',
     'Allow forwarding between ZeroTier members and LAN devices. Configure the LAN route in the ZeroTier controller; this does not grant access to the WAN or other VPNs.',
     'Дозволити переспрямування між учасниками ZeroTier і пристроями LAN. Налаштуйте маршрут до LAN у контролері ZeroTier; це не дає доступу до WAN чи інших VPN.',
     'Разрешить пересылку между участниками ZeroTier и устройствами LAN. Настройте маршрут к LAN в контроллере ZeroTier; это не даёт доступа к WAN или другим VPN.'),
    ('ZT_Off', 'Off', 'Вимкнено', 'Выключено'),
    ('ZT_On', 'On', 'Увімкнено', 'Включено'),
    ('ZT_Leave', 'Leave network', 'Вийти з мережі', 'Выйти из сети'),
    ('ZT_JoinHelp',
     'Enter a Network ID and Apply to join. Authorize the router in ZeroTier Central. Disabling the service preserves membership.',
     'Введіть ідентифікатор мережі та натисніть «Застосувати», щоб приєднатися. Авторизуйте роутер у ZeroTier Central. Вимкнення служби зберігає членство.',
     'Введите идентификатор сети и нажмите «Применить», чтобы присоединиться. Авторизуйте роутер в ZeroTier Central. Выключение службы сохраняет членство.'),
    ('ZT_Stale', 'Status is stale', 'Дані застаріли', 'Данные устарели'),
    ('ZT_Unknown', 'Unknown', 'Невідомо', 'Неизвестно'),
    ('ZT_Updated', 'Updated', 'Оновлено', 'Обновлено'),
    ('ZT_SecondsAgo', 'seconds ago', 'с тому', 'секунд назад'),
    ('ZT_Unavailable', 'Status is not available yet.', 'Стан ще недоступний.', 'Состояние пока недоступно.'),
    ('ZT_RefreshFailed', 'Could not refresh the status. Try again.',
     'Не вдалося оновити стан. Спробуйте ще раз.', 'Не удалось обновить состояние. Попробуйте снова.'),
]

# Inherited Chinese text, replaced by a dictionary key.
INHERITED = [
    ('已禁用', '<#ZT_Disabled#>'),
    ('已启用', '<#ZT_Enabled#>'),
    ('Zerotier官网', '<#ZT_OfficialSite#>'),
    ('Zerotier是一个开源、跨平台，而且适合内网穿透互联的傻瓜配置虚拟 VPN LAN', '<#ZT_IntroLine1#>'),
    ('新建或者管理网络，并允许客户端接入访问你私人网路（新接入的节点默认不允许访问）。', '<#ZT_IntroLine2#>'),
    ('启用ZeroTier客户端', '<#ZT_EnableClient#>'),
    ('ZeroTier 客户端 ID', '<#ZT_ClientID#>'),
    ('允许客户端NAT', '<#ZT_AllowNAT#>'),
    ('允许Zerotier的拨入客户端访问路由器LAN资源（需要在 Zerotier管理页面设定到LAN网段的路由表）', '<#ZT_NatHelp#>'),
    ('启用ZeroTier Moon服务器', '<#ZT_MoonEnable#>'),
    ('ZeroTier Moon服务器 IP or DomainName', '<#ZT_MoonEndpoint#>'),
    ('如果没有填写，将使用Wan获得的IP；如果填写IP地址，将使用该IP；如果填写域名，将使用域名获得IP（请注意为公网IP）。', '<#ZT_MoonEndpointHelp#>'),
    ('ZeroTier Moon服务器 ID', '<#ZT_MoonID#>'),
    ('服务器启用后自动生成Moon服务器的ID，在加入Moon时请使用客户端zerotier-cli orbit <该ID> <该ID>。', '<#ZT_MoonIDHelp#>'),
    ('需要访问其它zerotier的内网LAN网段,IP和网关和zerotier后台对应即可(本机的LAN网段不用填进去)', '<#ZT_RoutesHelp#>'),
    ('启用 <i class="icon-circle-arrow-down"></i>', '<#ZT_ColEnable#> <i class="icon-circle-arrow-down"></i>'),
    ('网关 <i class="icon-circle-arrow-down"></i>', '<#ZT_ColGateway#> <i class="icon-circle-arrow-down"></i>'),
    ('>是</option>', '><#ZT_Yes#></option>'),
    ('>否</option>', '><#ZT_No#></option>'),
]

# English text added by the earlier ZeroTier port steps, replaced by a key.
CONTROLS = [
    ('<th>Node and network status</th>', '<th><#ZT_StatusHeading#></th>'),
    ('<tr><th>Allow access to this router</th>', '<tr><th><#ZT_RouterAccess#></th>'),
    ('<tr><th>Allow access to LAN</th>', '<tr><th><#ZT_LanAccess#></th>'),
    ('>Leave network</button>', '><#ZT_Leave#></button>'),
    ('>Off</option>', '><#ZT_Off#></option>'),
    ('>On</option>', '><#ZT_On#></option>'),
    ('var stext = "Unknown";', 'var stext = "<#ZT_Unknown#>";'),
]

# Help blocks added by earlier steps. Matched by a unique prefix and closing tag
# so the exact wording stays owned by this script.
HELP_BLOCKS = [
    ('<small>Reload this page to refresh', '</small>',
     '<small><#ZT_StatusHelp#></small>', 'status help'),
    ('<p>Allow ZeroTier members to reach router services', '</p>',
     '<p><#ZT_RouterAccessHelp#></p>', 'router access help'),
    ('<p>Allow forwarding between ZeroTier members and LAN devices', '</p>',
     '<p><#ZT_LanAccessHelp#></p>', 'LAN access help'),
    ('<p>Enter a Network ID and Apply to join', '</p>',
     '<p><#ZT_JoinHelp#></p>', 'join help'),
]

RELOAD_BUTTON = ('<input type="button" id="btn_reconnect" class="btn btn-info" value="刷新页面" '
                 'onclick="window.location.reload();">')
REFRESH_CONTROL = ('<input type="button" id="btn_reconnect" class="btn btn-info" value="<#ZT_Refresh#>" '
                   'onclick="wrZerotierRefresh();">\n'
                   '\t\t\t\t\t\t\t\t\t<span id="zerotier_state_info" role="status" aria-live="polite"></span>')

JS_BLOCK = '''var wrZerotierBusy = false;
var wrZerotierTimer = null;
function wrZerotierApplyState(state) {
	// Cache freshness does not prove daemon health or overlay connectivity.
	var labels = ["<#ZT_Disabled#>", "<#ZT_Updated#>", "<#ZT_Stale#>", "<#ZT_Unknown#>"];
	$j("#zerotier_status").html('<span class="label label-' + (state === 1 ? 'success' : 'warning') + '">' +
		(labels[state] || labels[3]) + '</span>');
}
function wrZerotierRefresh() {
	if (wrZerotierBusy || document.hidden) return;
	wrZerotierBusy = true;
	$j.ajax({url: "/update.cgi", data: {output: "zerotier_state"}, dataType: "json", cache: false, timeout: 5000})
		.done(function (result) {
			var valid = result && typeof result.state === "number" &&
				result.state >= 0 && result.state <= 3 && result.state % 1 === 0 &&
				typeof result.age === "number" && isFinite(result.age) &&
				result.age % 1 === 0 && (result.state === 1 ? result.age >= 0 && result.age <= 60 :
				result.state === 2 ? result.age > 60 : result.age === -1);
			valid = valid && typeof result.text === "string" && result.text.length <= 4096;
			var state = valid ? result.state : 3;
			wrZerotierApplyState(state);
			$j("#zerotier_cached_text").text(valid && (state === 1 || state === 2) ? result.text : "<#ZT_Unavailable#>");
			var info = "";
			if (state === 1) info = "<#ZT_Updated#> " + result.age + " <#ZT_SecondsAgo#>";
			else if (state === 2) info = "<#ZT_Stale#> " + result.age + " <#ZT_SecondsAgo#>";
			else if (state === 3) info = "<#ZT_Unavailable#>";
			$j("#zerotier_state_info").text(info);
		})
		.fail(function () {
			wrZerotierApplyState(3);
			$j("#zerotier_cached_text").text("<#ZT_Unavailable#>");
			$j("#zerotier_state_info").text("<#ZT_RefreshFailed#>");
		})
		.always(function () { wrZerotierBusy = false; });
}
function wrZerotierStartAutoRefresh() {
	if (wrZerotierTimer !== null) return;
	wrZerotierTimer = window.setInterval(function () { wrZerotierRefresh(); }, 30000);
	document.addEventListener("visibilitychange", function () { if (!document.hidden) wrZerotierRefresh(); });
}
'''

INIT_ANCHOR = '\tfill_status(zerotier_status());'
INIT_REPLACEMENT = INIT_ANCHOR + '\n\twrZerotierRefresh();\n\twrZerotierStartAutoRefresh();'

BACKEND_ANCHOR = 'struct ej_handler ej_handlers[] =\n'
BACKEND_ENTRY = '\t{ "json_system_status", ej_system_status_hook},\n'
BACKEND_CODE = r'''
/* 0 disabled, 1 fresh, 2 stale, 3 unavailable. Bounded JSON for the WebUI. */
static int ej_zerotier_state(int eid, webs_t wp, int argc, char **argv)
{
	int state = 3;
	long age = -1;
	time_t now = time(NULL);
	struct stat status;
	FILE *cache = NULL;
	int ch;
	unsigned int count = 0;
	(void)eid; (void)argc; (void)argv;
	if (nvram_get_int("zerotier_enable") <= 0) {
		state = 0;
	} else if (!(cache = fopen("/var/run/zerotier-state.txt", "r")) ||
	           fstat(fileno(cache), &status) != 0) {
		state = 3;
	} else if (!S_ISREG(status.st_mode) || now <= 0 || status.st_mtime > now) {
		/* Clock rollback or an invalid cache must not look fresh. */
		state = 3;
	} else {
		age = (long)(now - status.st_mtime);
		state = age <= 60 ? 1 : 2;
	}
	websWrite(wp, "{\"state\":%d,\"age\":%ld,\"text\":\"", state, age);
	/* Same open snapshot for its age and content; never execute CLI in HTTP. */
	if (cache && (state == 1 || state == 2)) {
		while (count < 4096 && (ch = fgetc(cache)) != EOF) {
			++count;
			switch (ch) {
			case '\\': websWrite(wp, "\\\\"); break;
			case '"': websWrite(wp, "\\\""); break;
			case '\n': websWrite(wp, "\\n"); break;
			case '\r': websWrite(wp, "\\r"); break;
			case '\t': websWrite(wp, "\\t"); break;
			default: websWrite(wp, "%c", ch >= 32 && ch <= 126 ? ch : '?');
			}
		}
	}
	if (cache) fclose(cache);
	return websWrite(wp, "\"}");
}
'''


def replace_once(text, old, new, what, occurrences=1):
    if text.count(old) != occurrences:
        raise SystemExit('ZeroTier %s anchor mismatch (%d matches): %r'
                         % (what, text.count(old), old[:70]))
    return text.replace(old, new)


if args.verify_image:
    root = args.source / 'trunk/romfs/www'
    page = (root / 'Advanced_zerotier.asp').read_text(encoding='utf-8')
    if CJK.search(page):
        raise SystemExit('Untranslated ZeroTier image text')
    for marker in ('<#ZT_Refresh#>', 'wrZerotierRefresh', 'zerotier_state_info',
                   'id="zerotier_cached_text"'):
        if marker not in page:
            raise SystemExit('Missing ZeroTier refresh control: ' + marker)
    if 'window.location.reload' in page:
        raise SystemExit('ZeroTier page still reloads the whole document')
    for index, name in enumerate(('EN.dict', 'UK.dict', 'RU.dict'), 1):
        dictionary = (root / name).read_text(encoding='utf-8').splitlines()
        for entry in LABELS:
            key = entry[0]
            values = [line.split('=', 1)[1] for line in dictionary if line.startswith(key + '=')]
            if values != [entry[index]]:
                raise SystemExit('Missing or changed ZeroTier translation: ' + name + '/' + key)
    print('PASS ZeroTier page labels, refresh controls and exact EN/UK/RU translations')
    raise SystemExit(0)

page_path = args.source / 'trunk/user/www/n56u_ribbon_fixed/Advanced_zerotier.asp'
backend_path = args.source / 'trunk/user/httpd/web_ex.c'
page = page_path.read_text(encoding='utf-8')
for old, new in INHERITED:
    page = replace_once(page, old, new, 'inherited label')
for old, new in CONTROLS:
    count = page.count(old)
    if count not in (1, 2):
        raise SystemExit('ZeroTier control anchor mismatch (%d matches): %r' % (count, old[:70]))
    page = page.replace(old, new)
for prefix, terminator, replacement, what in HELP_BLOCKS:
    pattern = re.compile(re.escape(prefix) + r'[^<]*' + re.escape(terminator))
    if len(pattern.findall(page)) != 1:
        raise SystemExit('ZeroTier %s anchor mismatch' % what)
    page = pattern.sub(replacement, page, count=1)
page = replace_once(page, RELOAD_BUTTON, REFRESH_CONTROL, 'reload button')
page = replace_once(page, 'function initial(){', JS_BLOCK + 'function initial(){', 'initial function')
page = replace_once(page, INIT_ANCHOR, INIT_REPLACEMENT, 'status initialisation')
page = replace_once(page, '<pre style="white-space: pre-wrap;">',
                    '<pre id="zerotier_cached_text" style="white-space: pre-wrap;">',
                    'cached status text')
if CJK.search(page):
    raise SystemExit('Untranslated ZeroTier text remains; no files written')

backend = backend_path.read_text(encoding='utf-8')
backend = replace_once(backend, BACKEND_ANCHOR, BACKEND_CODE + '\n' + BACKEND_ANCHOR, 'handler table')
backend = replace_once(backend, BACKEND_ENTRY,
                       BACKEND_ENTRY + '\t{ "zerotier_state", ej_zerotier_state},\n', 'handler entry')

changes = [(page_path, page), (backend_path, backend)]
for index, name in enumerate(('EN.footer', 'UK.dict', 'RU.dict'), 1):
    path = args.source / 'trunk/user/www/dict' / name
    dictionary = path.read_text(encoding='utf-8')
    keys = {line.split('=', 1)[0] for line in dictionary.splitlines() if '=' in line}
    additions = []
    for entry in LABELS:
        if entry[0] in keys:
            raise SystemExit('ZeroTier translation key already exists: ' + entry[0])
        additions.append(entry[0] + '=' + entry[index])
    changes.append((path, dictionary.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'))

for path, content in changes:
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
print('Localized the ZeroTier page for EN/UK/RU and staged the bounded status refresh; runtime unverified')
