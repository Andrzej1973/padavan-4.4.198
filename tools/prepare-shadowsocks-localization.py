#!/usr/bin/env python3
"""Localize the visible Shadowsocks client/settings page controls (EN/UK/RU).

This source overlay only replaces UI text. It deliberately preserves every
HTML value, NVRAM key, protocol parameter, command and service behavior.
"""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify-image', action='store_true')
args = parser.parse_args()

LABELS = [
    ('SSLocTabClient', 'Client', 'Клієнт', 'Клиент'),
    ('SSLocTabNodes', 'Node management', 'Керування вузлами', 'Управление узлами'),
    ('SSLocTabAdvanced', 'Advanced settings', 'Додаткові налаштування', 'Дополнительные настройки'),
    ('SSLocTabRules', 'Rules', 'Правила', 'Правила'),
    ('SSLocTabLog', 'Runtime log', 'Журнал роботи', 'Журнал работы'),
    ('SSLocTabHelp', 'Help', 'Довідка', 'Справка'),
    ('SSLocIntro', 'A multi-protocol traffic routing tool supporting Shadowsocks, ShadowsocksR, Vmess, Vless, Trojan and SOCKS5.', 'Інструмент маршрутизації трафіку з підтримкою Shadowsocks, ShadowsocksR, Vmess, Vless, Trojan і SOCKS5.', 'Инструмент маршрутизации трафика с поддержкой Shadowsocks, ShadowsocksR, Vmess, Vless, Trojan и SOCKS5.'),
    ('SSLocAttention', 'Note:', 'Увага:', 'Внимание:'),
    ('SSLocEditWarning', 'If you edit a node that is currently in use, click Apply settings below after editing, then reconnect to apply the changes.', 'Якщо редагуєте вузол, який зараз використовується, після редагування натисніть «Застосувати», а потім перепідключіться.', 'Если вы редактируете используемый узел, после изменений нажмите «Применить», затем переподключитесь.'),
    ('SSLocRefreshWarning', 'The status is not updated in real time. After starting the service, wait briefly and use this button to refresh it.', 'Стан не оновлюється миттєво. Після запуску служби зачекайте трохи й натисніть цю кнопку, щоб оновити його.', 'Состояние обновляется не мгновенно. После запуска службы немного подождите и нажмите эту кнопку для обновления.'),
    ('SSLocDomesticIP', 'Mainland China IP address:', 'IP-адреса материкового Китаю:', 'IP-адрес материкового Китая:'),
    ('SSLocForeignIP', 'Overseas IP address:', 'Закордонна IP-адреса:', 'Зарубежный IP-адрес:'),
    ('SSLocGoogleStatus', 'Google connectivity:', 'Доступ до Google:', 'Доступ к Google:'),
    ('SSLocMainServer', 'Main server:', 'Основний сервер:', 'Основной сервер:'),
    ('SSLocDisabled', 'Disabled', 'Вимкнено', 'Отключено'),
    ('SSLocGameRelay', 'Game UDP relay server:', 'UDP-сервер-посередник для ігор:', 'UDP-сервер-посредник для игр:'),
    ('SSLocSameAsMain', 'Same as main server', 'Як основний сервер', 'Как основной сервер'),
    ('SSLocThreads', 'Parallel forwarding threads:', 'Потоки паралельного переспрямування:', 'Потоки параллельной переадресации:'),
    ('SSLocAutoCpu', 'Automatic (number of CPU threads)', 'Автоматично (за кількістю потоків ЦП)', 'Автоматически (по числу потоков ЦП)'),
    ('SSLocSingleThread', 'Single thread', 'Один потік', 'Один поток'),
    ('SSLocThreads2', '2 threads', '2 потоки', '2 потока'),
    ('SSLocThreads4', '4 threads', '4 потоки', '4 потока'),
    ('SSLocThreads8', '8 threads', '8 потоків', '8 потоков'),
    ('SSLocThreads16', '16 threads', '16 потоків', '16 потоков'),
    ('SSLocThreads24', '24 threads', '24 потоки', '24 потока'),
    ('SSLocRunMode', 'Routing mode:', 'Режим маршрутизації:', 'Режим маршрутизации:'),
    ('SSLocGfwMode', 'GFW list mode', 'За списком GFW', 'По списку GFW'),
    ('SSLocBypassChina', 'Bypass mainland China IP addresses', 'Обхід IP-адрес материкового Китаю', 'Обход IP-адрес материкового Китая'),
    ('SSLocGlobalMode', 'Global mode', 'Глобальний режим', 'Глобальный режим'),
    ('SSLocOverseaMode', 'Route overseas users to their home network', 'Повернення закордонних користувачів у домашню мережу', 'Возврат зарубежных пользователей в домашнюю сеть'),
    ('SSLocProxyPorts', 'Ports to proxy:', 'Порти через проксі:', 'Порты через прокси:'),
    ('SSLocAllPorts', 'All ports (default)', 'Усі порти (типово)', 'Все порты (по умолчанию)'),
    ('SSLocCommonPorts', 'Common ports only (P2P traffic bypasses the proxy)', 'Лише поширені порти (P2P-трафік іде повз проксі)', 'Только распространённые порты (P2P-трафик идёт мимо прокси)'),
    ('SSLocLanIPControl', 'LAN IP routing:', 'Маршрутизація IP-адрес LAN:', 'Маршрутизация IP-адресов LAN:'),
    ('SSLocAllViaProxy', 'Route all through proxy', 'Увесь трафік через проксі', 'Весь трафик через прокси'),
    ('SSLocSelectedViaProxy', 'Route selected IP addresses through proxy', 'Вибрані IP-адреси через проксі', 'Выбранные IP-адреса через прокси'),
    ('SSLocDnsMethod', 'DNS proxy method (dnsproxy recommended):', 'Метод DNS-проксі (рекомендовано dnsproxy):', 'Метод DNS-прокси (рекомендуется dnsproxy):'),
    ('SSLocDnsproxy', 'Use dnsproxy', 'Використовувати dnsproxy', 'Использовать dnsproxy'),
    ('SSLocDns2tcp', 'Use dns2tcp', 'Використовувати dns2tcp', 'Использовать dns2tcp'),
    ('SSLocChinaDns', 'Load ChinaDNS-NG (bypass modes only):', 'Завантажувати ChinaDNS-NG (лише в режимах обходу):', 'Загружать ChinaDNS-NG (только в режимах обхода):'),
    ('SSLocDomesticDns', 'Domestic DNS (ChinaDNS-NG only):', 'Внутрішній DNS (лише для ChinaDNS-NG):', 'Внутренний DNS (только для ChinaDNS-NG):'),
    ('SSLocForeignDns', 'External DNS:', 'Зовнішній DNS:', 'Внешний DNS:'),
    ('SSLocSmartDnsMode', 'SmartDNS startup mode:', 'Режим запуску SmartDNS:', 'Режим запуска SmartDNS:'),
    ('SSLocAutomatic', 'Automatic', 'Автоматично', 'Автоматически'),
    ('SSLocManual', 'Manual', 'Вручну', 'Вручную'),
    ('SSLocSubscriptionNotice', 'After adding subscription URLs, click Apply settings first, then Update subscription to fetch the nodes.', 'Після додавання адрес підписки спочатку натисніть «Застосувати», а потім «Оновити підписку», щоб завантажити вузли.', 'После добавления адрес подписки сначала нажмите «Применить», затем «Обновить подписку», чтобы загрузить узлы.'),
    ('SSLocSubscriptionUrls', 'Enter node subscription URLs (one URL per line)', 'Введіть адреси підписки на вузли (по одній адресі в рядку)', 'Введите адреса подписки на узлы (по одному адресу в строке)'),
    ('SSLocDiscardKeywords', 'Nodes matching these keywords will be discarded. Separate multiple keywords with /.', 'Вузли, що містять ці ключові слова, буде відкинуто. Розділяйте слова символом /.', 'Узлы с этими ключевыми словами будут отброшены. Разделяйте слова символом /.'),
    ('SSLocAllNodes', 'All nodes', 'Усі вузли', 'Все узлы'),
    ('SSLocCustomNodes', 'Custom nodes', 'Власні вузли', 'Собственные узлы'),
    ('SSLocSubscribedNodes', 'Subscribed nodes', 'Вузли з підписки', 'Узлы из подписки'),
    ('SSLocUpdateSubscription', 'Update subscription', 'Оновити підписку', 'Обновить подписку'),
    ('SSLocAddImportNode', 'Add / import node', 'Додати / імпортувати вузол', 'Добавить / импортировать узел'),
    ('SSLocPingSelected', 'Ping selected nodes', 'Перевірити вибрані вузли', 'Проверить выбранные узлы'),
    ('SSLocPingAll', 'Ping all nodes', 'Перевірити всі вузли', 'Проверить все узлы'),
    ('SSLocDeleteSelected', 'Delete selected nodes', 'Видалити вибрані вузли', 'Удалить выбранные узлы'),
    ('SSLocDeleteAll', 'Delete all nodes', 'Видалити всі вузли', 'Удалить все узлы'),
    ('SSLocNodeEditor', 'Add, delete or edit node', 'Додати, видалити або змінити вузол', 'Добавить, удалить или изменить узел'),
    ('SSLocImportNodeInfo', 'Import node configuration:', 'Імпорт конфігурації вузла:', 'Импорт конфигурации узла:'),
    ('SSLocEnterNodeUrl', 'Paste node URL', 'Вставити URL вузла', 'Вставить URL узла'),
    ('SSLocNodeType', 'Node type:', 'Тип вузла:', 'Тип узла:'),
    ('SSLocAliasOptional', 'Alias (optional):', 'Назва (необов’язково):', 'Название (необязательно):'),
    ('SSLocServerAddress', 'Server address:', 'Адреса сервера:', 'Адрес сервера:'),
    ('SSLocServerPort', 'Server port:', 'Порт сервера:', 'Порт сервера:'),
    ('SSLocServerPassword', 'Server password:', 'Пароль сервера:', 'Пароль сервера:'),
    ('SSLocEncryptionMethod', 'Encryption method:', 'Метод шифрування:', 'Метод шифрования:'),
    ('SSLocEncryptionLabel', 'Encryption:', 'Шифрування:', 'Шифрование:'),
    ('SSLocProtocol', 'Protocol:', 'Протокол:', 'Протокол:'),
    ('SSLocPlugin', 'Plugin:', 'Плагін:', 'Плагин:'),
    ('SSLocPluginOptions', 'Plugin options:', 'Параметри плагіна:', 'Параметры плагина:'),
    ('SSLocTransportOptions', 'Transport protocol options (optional):', 'Параметри транспортного протоколу (необов’язково):', 'Параметры транспортного протокола (необязательно):'),
    ('SSLocObfuscation', 'Obfuscation:', 'Маскування:', 'Маскировка:'),
    ('SSLocObfuscationOptions', 'Obfuscation options (optional):', 'Параметри маскування (необов’язково):', 'Параметры маскировки (необязательно):'),
    ('SSLocUserPassAuth', 'Enable username/password authentication:', 'Увімкнути автентифікацію за ім’ям і паролем:', 'Включить аутентификацию по имени и паролю:'),
    ('SSLocUsername', 'Username:', 'Ім’я користувача:', 'Имя пользователя:'),
    ('SSLocPassword', 'Password:', 'Пароль:', 'Пароль:'),
    ('SSLocTransport', 'Transport:', 'Транспорт:', 'Транспорт:'),
    ('SSLocObfuscationType', 'Obfuscation type:', 'Тип маскування:', 'Тип маскировки:'),
    ('SSLocNotConfigured', 'Not configured', 'Не налаштовано', 'Не настроено'),
    ('SSLocSaveNode', 'Save node', 'Зберегти вузол', 'Сохранить узел'),
    ('SSLocCancel', 'Cancel', 'Скасувати', 'Отмена'),
    ('SSLocDeleteColumn', 'Delete', 'Видалити', 'Удалить'),
    ('SSLocIndex', 'No.', '№', '№'),
    ('SSLocTypeColumn', 'Type', 'Тип', 'Тип'),
    ('SSLocAliasColumn', 'Alias', 'Назва', 'Название'),
    ('SSLocServerColumn', 'Server address', 'Адреса сервера', 'Адрес сервера'),
    ('SSLocPacketLoss', 'Packet loss', 'Втрата пакетів', 'Потеря пакетов'),
    ('SSLocActions', 'Actions', 'Дії', 'Действия'),
    ('SSLocProcessLimits', 'Process resource limits', 'Обмеження ресурсів процесу', 'Ограничение ресурсов процесса'),
    ('SSLocEnableProcessLimits', 'Enable process resource limits:', 'Увімкнути обмеження ресурсів процесу:', 'Включить ограничение ресурсов процесса:'),
    ('SSLocCpuLimit', 'CPU limit:', 'Обмеження ЦП:', 'Ограничение ЦП:'),
    ('SSLocMemoryLimit', 'Memory limit:', 'Обмеження пам’яті:', 'Ограничение памяти:'),
    ('SSLocProcessWatchdog', 'Process watchdog:', 'Контроль процесу:', 'Контроль процесса:'),
    ('SSLocSocks5Proxy', 'SOCKS5 proxy', 'Проксі SOCKS5', 'Прокси SOCKS5'),
    ('SSLocServer', 'Server:', 'Сервер:', 'Сервер:'),
    ('SSLocLocalPort', 'Local port:', 'Локальний порт:', 'Локальный порт:'),
    ('SSLocGameModeTitle', 'Game-mode client: UDP uses all ports; TCP follows the main server port; bypass-China mode is forced.', 'Ігровий режим клієнта: UDP використовує всі порти, TCP — порт основного сервера; примусово ввімкнено режим обходу Китаю.', 'Игровой режим клиента: UDP использует все порты, TCP — порт основного сервера; принудительно включён режим обхода Китая.'),
    ('SSLocGameLanIps', 'Game-mode LAN IP addresses:', 'IP-адреси LAN для ігрового режиму:', 'IP-адреса LAN для игрового режима:'),
    ('SSLocBypassLanIps', 'LAN IP addresses bypassing Shadowsocks:', 'IP-адреси LAN без Shadowsocks:', 'IP-адреса LAN без Shadowsocks:'),
    ('SSLocForceLanIps', 'LAN IP addresses forced through Shadowsocks:', 'IP-адреси LAN примусово через Shadowsocks:', 'IP-адреса LAN принудительно через Shadowsocks:'),
    ('SSLocBypassWanIps', 'WAN IP addresses bypassing Shadowsocks:', 'WAN IP-адреси без Shadowsocks:', 'WAN IP-адреса без Shadowsocks:'),
    ('SSLocForceWanIps', 'WAN IP addresses forced through Shadowsocks:', 'WAN IP-адреси примусово через Shadowsocks:', 'WAN IP-адреса принудительно через Shadowsocks:'),
    ('SSLocBypassDomains', 'Domains bypassing Shadowsocks:', 'Домени без Shadowsocks:', 'Домены без Shadowsocks:'),
    ('SSLocForceDomains', 'Domains forced through Shadowsocks:', 'Домени примусово через Shadowsocks:', 'Домены принудительно через Shadowsocks:'),
    ('SSLocChinaDnsHelpTitle', 'ChinaDNS-NG notes', 'Про ChinaDNS-NG', 'О ChinaDNS-NG'),
    ('SSLocChinaDnsHelp', 'In bypass-China mode, ChinaDNS-NG loads CDN domain rules to direct common sites to domestic DNS and the GFW list to direct other sites to external DNS.', 'У режимі обходу Китаю ChinaDNS-NG використовує правила CDN-доменів для спрямування поширених сайтів на внутрішній DNS, а список GFW — на зовнішній DNS.', 'В режиме обхода Китая ChinaDNS-NG использует правила CDN-доменов для направления популярных сайтов на внутренний DNS, а список GFW — на внешний DNS.'),
    ('SSLocChinaDnsMemoryWarning', 'This mode uses additional memory. Enable it cautiously on devices with limited RAM.', 'Цей режим використовує додаткову пам’ять. На пристроях із малою кількістю ОЗП вмикайте його обережно.', 'Этот режим использует дополнительную память. На устройствах с малым объёмом ОЗУ включайте его осторожно.'),
    ('SSLocResourceLimitsHelp', 'Process resource limits use cgroups.', 'Обмеження ресурсів процесу використовують cgroups.', 'Ограничение ресурсов процесса использует cgroups.'),
    ('SSLocRunningScript', 'Running script:', 'Виконується сценарій:', 'Выполняется сценарий:'),
    ('SSLocScriptComplete', 'Script completed.', 'Сценарій завершено.', 'Сценарий завершён.'),
    ('SSLocScriptSuccess', 'The operation completed successfully.', 'Операцію виконано успішно.', 'Операция выполнена успешно.'),
    ('SSLocScriptFailed', 'The operation failed. Please try again.', 'Не вдалося виконати операцію. Спробуйте ще раз.', 'Не удалось выполнить операцию. Попробуйте ещё раз.'),
    ('SSLocUpdatingSubscription', 'Updating node subscriptions…', 'Оновлення підписок на вузли…', 'Обновление подписок на узлы…'),
    ('SSLocDeletingAllNodes', 'Deleting all nodes…', 'Видалення всіх вузлів…', 'Удаление всех узлов…'),
    ('SSLocDeletingSelectedNodes', 'Deleting selected nodes…', 'Видалення вибраних вузлів…', 'Удаление выбранных узлов…'),
    ('SSLocPingingSelectedNodes', 'Checking selected nodes…', 'Перевірка вибраних вузлів…', 'Проверка выбранных узлов…'),
    ('SSLocPingingAllNodes', 'Checking all nodes…', 'Перевірка всіх вузлів…', 'Проверка всех узлов…'),
    ('SSLocDeleteFailed', 'Could not delete the node. Please try again.', 'Не вдалося видалити вузол. Спробуйте ще раз.', 'Не удалось удалить узел. Попробуйте ещё раз.'),
    ('SSLocDeleteConfirm', 'Delete node “', 'Видалити вузол «', 'Удалить узел «'),
    ('SSLocConfirmSuffix', '”?', '»?', '»?'),
    ('SSLocEditNode', 'Edit node', 'Змінити вузол', 'Изменить узел'),
    ('SSLocCopyNode', 'Copy node', 'Копіювати вузол', 'Копировать узел'),
    ('SSLocNodeTypeUnavailable', 'Type unavailable', 'Тип невідомий', 'Тип неизвестен'),
    ('SSLocNodeNameUnavailable', 'Name unavailable', 'Назва невідома', 'Название неизвестно'),
    ('SSLocImportSsSuccess', 'Shadowsocks configuration imported.', 'Конфігурацію Shadowsocks імпортовано.', 'Конфигурация Shadowsocks импортирована.'),
    ('SSLocImportSsrSuccess', 'ShadowsocksR configuration imported.', 'Конфігурацію ShadowsocksR імпортовано.', 'Конфигурация ShadowsocksR импортирована.'),
    ('SSLocImportTrojanSuccess', 'Trojan configuration imported.', 'Конфігурацію Trojan імпортовано.', 'Конфигурация Trojan импортирована.'),
    ('SSLocImportV2raySuccess', 'V2Ray configuration imported.', 'Конфігурацію V2Ray імпортовано.', 'Конфигурация V2Ray импортирована.'),
    ('SSLocImportXraySuccess', 'Xray configuration imported.', 'Конфігурацію Xray імпортовано.', 'Конфигурация Xray импортирована.'),
    ('SSLocEditAction', 'Edit', 'Змінити', 'Изменить'),
    ('SSLocCopyAction', 'Copy', 'Копіювати', 'Копировать'),
    ('SSLocAddImportTitle', 'Add / import node', 'Додати / імпортувати вузол', 'Добавить / импортировать узел'),
    ('SSLocPasteConfigUrl', 'Paste a configuration URL (ssr://, ss://, vmess://, vless:// or trojan://):', 'Вставте URL конфігурації (ssr://, ss://, vmess://, vless:// або trojan://):', 'Вставьте URL конфигурации (ssr://, ss://, vmess://, vless:// или trojan://):'),
    ('SSLocImportCancelled', 'Import cancelled.', 'Імпорт скасовано.', 'Импорт отменён.'),
    ('SSLocInvalidFormat', 'Invalid configuration link format.', 'Неправильний формат посилання конфігурації.', 'Неверный формат ссылки конфигурации.'),
    ('SSLocLocalDns', 'Local DNS ', 'Локальний DNS ', 'Локальный DNS '),
    ('SSLocCannotReach', 'Unavailable', 'Недоступно', 'Недоступно'),
    ('SSLocRefreshButton', 'Refresh status', 'Оновити стан', 'Обновить состояние'),
    ('SSLocRefreshPage', 'Refresh page', 'Оновити сторінку', 'Обновить страницу'),
    ('SSLocAutoSwitchType', 'Automatic switch type:', 'Тип автоматичного перемикання:', 'Тип автоматического переключения:'),
    ('SSLocProcessLimitsPurpose', 'Resource limits help prevent the service from using too much memory or CPU and making the router slow or causing a reboot. You can raise the limits if the router has enough resources.', 'Обмеження ресурсів допомагають не допустити надмірного використання пам’яті чи ЦП, уповільнення роботи або перезапуску роутера. Якщо ресурсів роутера достатньо, ліміти можна збільшити.', 'Ограничения ресурсов помогают не допустить чрезмерного использования памяти или ЦП, замедления работы либо перезагрузки роутера. Если ресурсов роутера достаточно, лимиты можно увеличить.'),
    ('SSLocCpuMemoryLimitHelp', 'CPU limit: an integer greater than 2 and less than 1024, expressed as a percentage (512 means 50%). Include M in the memory limit, for example 20M. The kernel OOM killer terminates the process if it exceeds that limit.', 'Ліміт ЦП — ціле число більше 2 і менше 1024, у відсотках (512 означає 50%). Для ліміту пам’яті вкажіть одиницю M, наприклад 20M. Якщо ліміт перевищено, ядро завершить процес через OOM killer.', 'Лимит ЦП — целое число больше 2 и меньше 1024, в процентах (512 означает 50%). Для лимита памяти укажите единицу M, например 20M. При превышении лимита ядро завершит процесс через OOM killer.'),
]


def strip_javascript_comments(source: str) -> str:
    """Remove JS comments while preserving quoted UI strings for localization checks."""
    output = []
    quote = None
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            output.append(char)
            if char == "\\" and index + 1 < len(source):
                index += 1
                output.append(source[index])
            elif char == quote:
                quote = None
        elif char in ("'", '"', '`'):
            quote = char
            output.append(char)
        elif source.startswith('//', index):
            end = source.find('\n', index)
            if end < 0:
                break
            output.append('\n')
            index = end
        elif source.startswith('/*', index):
            end = source.find('*/', index + 2)
            if end < 0:
                break
            index = end + 1
        else:
            output.append(char)
        index += 1
    return ''.join(output)

# Exact visible labels/options in the inherited page. Configuration values
# (the value= attributes and NVRAM calls) are not included in these anchors.
REPLACEMENTS = [
    ('>客户端</a>', '><#SSLocTabClient#></a>'),
    ('>节点管理</a>', '><#SSLocTabNodes#></a>'),
    ('>高级设置</a>', '><#SSLocTabAdvanced#></a>'),
    ('>规则管理</a>', '><#SSLocTabRules#></a>'),
    ('>运行日志</a>', '><#SSLocTabLog#></a>'),
    ('>帮助文档</a>', '><#SSLocTabHelp#></a>'),
    ('一个兼容Shadowsocks、ShadowsocksR 、Vmess、Vless、Trojan、Sock5协议的游戏加速工具。', '<#SSLocIntro#>'),
    ('若被编辑的节点正在运行使用，请编辑完成后点击下方“应用设置”按钮更新节点信息，并点击"重连"按钮重新连接。', '<#SSLocEditWarning#>'),
    ('运行状态不会实时更新，启动程序后需稍等片刻，再点击此 <input type="button" id="btn_reconnect" class="btn btn-info" value="刷新页面" onclick="window.location.reload();" tabindex="1"> 按钮重新获取运行状态。', '<#SSLocRefreshWarning#> <input type="button" id="btn_reconnect" class="btn btn-info" value="<#SSLocRefreshButton#>" onclick="window.location.reload();" tabindex="1">'),
    ('value="刷新页面"', 'value="<#SSLocRefreshPage#>"'),
    ('value="正在运行脚本:0s"', 'value="<#SSLocRunningScript#>0s"'),
    ('国内IP：', '<#SSLocDomesticIP#>'), ('国外IP：', '<#SSLocForeignIP#>'),
    ('Google 访问状态：', '<#SSLocGoogleStatus#>'), ('主服务器：', '<#SSLocMainServer#>'),
    ('游戏UDP中继服务器：', '<#SSLocGameRelay#>'), ('多线程并发转发：', '<#SSLocThreads#>'),
    ('>停用</option>', '><#SSLocDisabled#></option>'),
    ('>与主服务相同</option>', '><#SSLocSameAsMain#></option>'),
    ('>自动（CPU线程数）</option>', '><#SSLocAutoCpu#></option>'), ('>单线程</option>', '><#SSLocSingleThread#></option>'),
    ('>2 线程</option>', '><#SSLocThreads2#></option>'), ('>4 线程</option>', '><#SSLocThreads4#></option>'),
    ('>8 线程</option>', '><#SSLocThreads8#></option>'), ('>16 线程</option>', '><#SSLocThreads16#></option>'),
    ('>24 线程</option>', '><#SSLocThreads24#></option>'), ('运行模式：', '<#SSLocRunMode#>'),
    ('>gfw列表模式</option>', '><#SSLocGfwMode#></option>'), ('>绕过大陆IP模式</option>', '><#SSLocBypassChina#></option>'),
    ('>全局模式</option>', '><#SSLocGlobalMode#></option>'), ('>海外用户回国模式</option>', '><#SSLocOverseaMode#></option>'),
    ('需要代理的端口：', '<#SSLocProxyPorts#>'), ('>所有端口（默认）</option>', '><#SSLocAllPorts#></option>'),
    ('>仅常用端口(不走P2P流量到代理)</option>', '><#SSLocCommonPorts#></option>'),
    ('内网IP控制：', '<#SSLocLanIPControl#>'), ('>全部走代理</option>', '><#SSLocAllViaProxy#></option>'),
    ('>指定IP走代理</option>', '><#SSLocSelectedViaProxy#></option>'),
    ('DNS代理解析方式：(推荐dnsproxy)', '<#SSLocDnsMethod#>'), ('>使用dnsproxy查询</option>', '><#SSLocDnsproxy#></option>'),
    ('>使用dns2tcp查询</option>', '><#SSLocDns2tcp#></option>'), ('加载chinadns-ng：(仅绕过模式生效)', '<#SSLocChinaDns#>'),
    ('国内DNS：(仅chinadns-ng生效)', '<#SSLocDomesticDns#>'), ('国外DNS：', '<#SSLocForeignDns#>'),
    ('SmartDNS加载方式:', '<#SSLocSmartDnsMode#>'), ('>自动配置', '><#SSLocAutomatic#>'),
    ('>手动配置', '><#SSLocManual#>'),
    ('<div class="alert alert-info" style="margin: 10px;"><span style="color:#E53333;">注意：</span> 添加完节点订阅地址后，请先点击下方“应用设置”按钮，再点击“更新订阅”按钮更新所订阅的节点。', '<div class="alert alert-info" style="margin: 10px;"><span style="color:#E53333;"><#SSLocAttention#></span> <#SSLocSubscriptionNotice#>'),
    ('注意：', '<#SSLocAttention#>'),
    ('<span>点击输入节点订阅地址：(一行一个地址)</span>', '<span><#SSLocSubscriptionUrls#></span>'),
    ('命中关键字的节点将被丢弃，多个关键字用 / 分隔。', '<#SSLocDiscardKeywords#>'),
    ('<option value="a">全部节点</option>', '<option value="a"><#SSLocAllNodes#></option>'),
    ('<option value="d">自定义节点</option>', '<option value="d"><#SSLocCustomNodes#></option>'),
    ('<option value="c">订阅节点</option>', '<option value="c"><#SSLocSubscribedNodes#></option>'),
    ('value="更新节点订阅"', 'value="<#SSLocUpdateSubscription#>"'),
    ('value="添加/导入节点"', 'value="<#SSLocAddImportNode#>"'),
    ('value="ping选中节点"', 'value="<#SSLocPingSelected#>"'),
    ('value="ping全部节点"', 'value="<#SSLocPingAll#>"'),
    ('value="删除选中节点"', 'value="<#SSLocDeleteSelected#>"'),
    ('value="删除全部节点"', 'value="<#SSLocDeleteAll#>"'),
    ('>添加/删除/编辑节点</th>', '><#SSLocNodeEditor#></th>'),
    ('>导入节点信息：</th>', '><#SSLocImportNodeInfo#></th>'),
    ('value="点击输入节点URL"', 'value="<#SSLocEnterNodeUrl#>"'),
    ('>服务器节点类型：</th>', '><#SSLocNodeType#></th>'),
    ('>别名：（可选）</th>', '><#SSLocAliasOptional#></th>'),
    ('>服务器IP地址：</th>', '><#SSLocServerAddress#></th>'),
    ('>服务器端口：</th>', '><#SSLocServerPort#></th>'),
    ('>服务器密码：</th>', '><#SSLocServerPassword#></th>'),
    ('>加密方式：</th>', '><#SSLocEncryptionMethod#></th>'),
    ('>加密：</th>', '><#SSLocEncryptionLabel#></th>'),
    ('>协议：</th>', '><#SSLocProtocol#></th>'),
    ('>插件：</th>', '><#SSLocPlugin#></th>'),
    ('>插件参数：</th>', '><#SSLocPluginOptions#></th>'),
    ('>传输协议参数：（可选）</th>', '><#SSLocTransportOptions#></th>'),
    ('>混淆：</th>', '><#SSLocObfuscation#></th>'),
    ('>混淆参数：（可选）</th>', '><#SSLocObfuscationOptions#></th>'),
    ('>启用用户名/密码认证：</th>', '><#SSLocUserPassAuth#></th>'),
    ('>用户名：</th>', '><#SSLocUsername#></th>'),
    ('>密码：</th>', '><#SSLocPassword#></th>'),
    ('>传输方式：</th>', '><#SSLocTransport#></th>'),
    ('>伪装类型：</th>', '><#SSLocObfuscationType#></th>'),
    ('>未配置</option>', '><#SSLocNotConfigured#></option>'),
    ('value="保存节点"', 'value="<#SSLocSaveNode#>"'),
    ('value="取消"', 'value="<#SSLocCancel#>"'),
    ("title: '删除'", "title: '<#SSLocDeleteColumn#>'"),
    ("title: '序号'", "title: '<#SSLocIndex#>'"),
    ("title: '类型'", "title: '<#SSLocTypeColumn#>'"),
    ("title: '别名'", "title: '<#SSLocAliasColumn#>'"),
    ("title: '服务器地址'", "title: '<#SSLocServerColumn#>'"),
    ("title: '丢包'", "title: '<#SSLocPacketLoss#>'"),
    ("title: '操作'", "title: '<#SSLocActions#>'"),
    ('>进程资源限制</th>', '><#SSLocProcessLimits#></th>'),
    ('>启用进程资源限制：</th>', '><#SSLocEnableProcessLimits#></th>'),
    ('>CPU 限制：</th>', '><#SSLocCpuLimit#></th>'),
    ('>内存限制：</th>', '><#SSLocMemoryLimit#></th>'),
    ('>进程守护：</th>', '><#SSLocProcessWatchdog#></th>'),
    ('>SOCKS5代理</th>', '><#SSLocSocks5Proxy#></th>'),
    ('>服务器：</th>', '><#SSLocServer#></th>'),
    ('>本地端口：</th>', '><#SSLocLocalPort#></th>'),
    ('>游戏模式客户端UDP所有端口,TCP跟随主服务器端口模式,强制走绕过大陆模式</th>', '><#SSLocGameModeTitle#></th>'),
    ('<span>游戏模式LAN IP:</span>', '<span><#SSLocGameLanIps#></span>'),
    ('<span>不走SS代理的LAN IP:</span>', '<span><#SSLocBypassLanIps#></span>'),
    ('<span>强制走SS代理的LAN IP:</span>', '<span><#SSLocForceLanIps#></span>'),
    ('<span>不走SS代理的WAN IP:</span>', '<span><#SSLocBypassWanIps#></span>'),
    ('<span>强制走SS代理的WAN IP:</span>', '<span><#SSLocForceWanIps#></span>'),
    ('<span>不走SS代理的域名:</span>', '<span><#SSLocBypassDomains#></span>'),
    ('<span>强制走SS代理的域名:</span>', '<span><#SSLocForceDomains#></span>'),
    ('>chinadns-ng说明:</th>', '><#SSLocChinaDnsHelpTitle#></th>'),
    ('>绕过大陆模式启用chinadns会加载CDN域名规则来分流常用网站跑国内DNS,加载gfwlist列表来分流到国外DNS</th>', '><#SSLocChinaDnsHelp#></th>'),
    ('>此模式会占用一部分内存资源,内存少的机器请谨慎开启。</th>', '><#SSLocChinaDnsMemoryWarning#></th>'),
    ('>进程资源限制说明: 此功能底层使用 <a href="https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v1/cgroups.html">cgroups</a></th>', '><#SSLocResourceLimitsHelp#></th>'),
    ('>自动切换类型：</th>', '><#SSLocAutoSwitchType#></th>'),
    ('>进程资源限制是为了防止进程占用过多资源导致路由器卡顿或重启,如果你的路由器配置足够,可以适当调高限制值。</th>', '><#SSLocProcessLimitsPurpose#></th>'),
    ('>CPU 限制值为一个大于 2 小于 1024 的整数，表示可以使用的 CPU 百分比，如 512 表示 50%;内存限制值需要带上 M 作为单位,<br/> 如 20M 表示可以使用 20M 内存，超出会被内核 OOM Killer 自动 kill。</th>', '><#SSLocCpuMemoryLimitHelp#></th>'),
    ('document.getElementById("ss_setting_title").innerHTML = "添加/导入节点";', 'document.getElementById("ss_setting_title").innerHTML = "<#SSLocAddImportTitle#>";'),
    ("document.getElementById('btn_ctime').value='正在运行脚本:0s';", "document.getElementById('btn_ctime').value='<#SSLocRunningScript#>0s';"),
    ("document.getElementById('btn_ctime').value='正在运行脚本:' + t +\"s\";", "document.getElementById('btn_ctime').value='<#SSLocRunningScript#>' + t +\"s\";"),
    ("document.getElementById('btn_ctime').value='脚本运行完成!';", "document.getElementById('btn_ctime').value='<#SSLocScriptComplete#>';"),
    ('alert("脚本执行成功...")', 'alert("<#SSLocScriptSuccess#>")'),
    ('document.getElementById("btn_update_link").value="正在更新节点订阅";', 'document.getElementById("btn_update_link").value="<#SSLocUpdatingSubscription#>";'),
    ('alert("脚本执行失败！！！")', 'alert("<#SSLocScriptFailed#>")'),
    ("document.getElementById('btn_update_link').value='更新节点订阅';", "document.getElementById('btn_update_link').value='<#SSLocUpdateSubscription#>';"),
    ('document.getElementById("btn_rest_link").value="正在删除全部节点";', 'document.getElementById("btn_rest_link").value="<#SSLocDeletingAllNodes#>";'),
    ("document.getElementById('btn_rest_link').value='删除全部节点';", "document.getElementById('btn_rest_link').value='<#SSLocDeleteAll#>';"),
    ('<a class="edit_ss" href="javascript:void(0)" title="编辑">编辑</a>', '<a class="edit_ss" href="javascript:void(0)" title="<#SSLocEditAction#>"><#SSLocEditAction#></a>'),
    ('<a class="copy_ss" href="javascript:void(0)" title="复制">复制</a>', '<a class="copy_ss" href="javascript:void(0)" title="<#SSLocCopyAction#>"><#SSLocCopyAction#></a>'),
    ('<a class="del_ss" href="javascript:void(0)" title="删除">删除</a>', '<a class="del_ss" href="javascript:void(0)" title="<#SSLocDeleteColumn#>"><#SSLocDeleteColumn#></a>'),
    ('document.getElementById("ss_setting_title").innerHTML = "编辑节点";', 'document.getElementById("ss_setting_title").innerHTML = "<#SSLocEditNode#>";'),
    ('document.getElementById("ss_setting_title").innerHTML = "复制节点";', 'document.getElementById("ss_setting_title").innerHTML = "<#SSLocCopyNode#>";'),
    ("confirm('确认删除' + row.alias + '吗？')", "confirm('<#SSLocDeleteConfirm#>' + row.alias + '<#SSLocConfirmSuffix#>')"),
    ('alert("删除失败,请重试！")', 'alert("<#SSLocDeleteFailed#>")'),
    ('document.getElementById("btn_del_link").value="正在删除选中节点";', 'document.getElementById("btn_del_link").value="<#SSLocDeletingSelectedNodes#>";'),
    ("document.getElementById('btn_del_link').value='删除选中节点';", "document.getElementById('btn_del_link').value='<#SSLocDeleteSelected#>';"),
    ('document.getElementById("btn_ping_link").value="正在ping选中节点";', 'document.getElementById("btn_ping_link").value="<#SSLocPingingSelectedNodes#>";'),
    ("document.getElementById('btn_ping_link').value='ping选中节点';", "document.getElementById('btn_ping_link').value='<#SSLocPingSelected#>';"),
    ('document.getElementById("btn_aping_link").value="正在ping全部节点";', 'document.getElementById("btn_aping_link").value="<#SSLocPingingAllNodes#>";'),
    ("document.getElementById('btn_aping_link').value='ping全部节点';", "document.getElementById('btn_aping_link').value='<#SSLocPingAll#>';"),
    ('"类型获取失败"', '"<#SSLocNodeTypeUnavailable#>"'),
    ('"名字获取失败"', '"<#SSLocNodeNameUnavailable#>"'),
    ("'<option value=\"'+wan0_dns+'\" selected>本地DNS ' + wan0_dns + '</option>'", "'<option value=\"'+wan0_dns+'\" selected><#SSLocLocalDns#>' + wan0_dns + '</option>'"),
    ('alt="无法访问"', 'alt="<#SSLocCannotReach#>"'),
    ('prompt("在这里粘贴配置链接 ssr:// | ss:// | vmess:// | vless:// | trojan://", "")', 'prompt("<#SSLocPasteConfigUrl#>", "")'),
    ('<font color=\'red\'>用户取消</font>', '<font color=\'red\'><#SSLocImportCancelled#></font>'),
    ('<font color=\'red\'>无效格式</font>', '<font color=\'red\'><#SSLocInvalidFormat#></font>'),
    ('导入ShadowsocksR配置信息成功', '<#SSLocImportSsrSuccess#>'),
    ('导入Shadowsocks配置信息成功', '<#SSLocImportSsSuccess#>'),
    ('导入Trojan配置信息成功', '<#SSLocImportTrojanSuccess#>'),
    ('导入V2ray配置信息成功', '<#SSLocImportV2raySuccess#>'),
    ('导入Xray配置信息成功', '<#SSLocImportXraySuccess#>'),
]

root = args.source
if args.verify_image:
    www = root / 'www'
    page = (www / 'Shadowsocks.asp').read_text(encoding='utf-8')
    visible_source = re.sub(r'<!--.*?-->', '', page, flags=re.DOTALL)
    visible_source = re.sub(
        r'(?is)<script\b[^>]*>.*?</script>',
        lambda match: strip_javascript_comments(match.group(0)),
        visible_source,
    )
    if re.search(r'[\u3400-\u4dbf\u4e00-\u9fff]', visible_source):
        raise SystemExit('Unlocalized CJK text remains in final Shadowsocks page')
    for filename, language_index in (('EN.dict', 0), ('UK.dict', 1), ('RU.dict', 2)):
        dictionary = (www / filename).read_text(encoding='utf-8').splitlines()
        for key, en, uk, ru in LABELS:
            values = [line.split('=', 1)[1] for line in dictionary if line.startswith(key + '=')]
            if values != [(en, uk, ru)[language_index]]:
                raise SystemExit(f'Missing or incorrect Shadowsocks translation: {filename}/{key}')
    print('PASS final ROMFS Shadowsocks page has no CJK UI text and all EN/UK/RU keys match')
    raise SystemExit(0)

page_path = root / 'trunk/user/www/n56u_ribbon_fixed/Shadowsocks.asp'
page = page_path.read_text(encoding='utf-8')
for old, new in REPLACEMENTS:
    count = page.count(old)
    if count < 1:
        raise SystemExit(f'Shadowsocks localization anchor missing: {old[:80]}')
    page = page.replace(old, new)

changes = [(page_path, page)]
for i, filename in enumerate(('EN.footer', 'UK.dict', 'RU.dict')):
    path = root / 'trunk/user/www/dict' / filename
    contents = path.read_text(encoding='utf-8')
    additions = []
    for key, en, uk, ru in LABELS:
        if any(line.startswith(key + '=') for line in contents.splitlines()):
            raise SystemExit(f'Shadowsocks translation key already exists: {key}')
        additions.append(f'{key}={(en, uk, ru)[i]}')
    changes.append((path, contents.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'))

for path, contents in changes:
    path.write_text(contents, encoding='utf-8', newline='\n')
print('Localized Shadowsocks navigation, client settings, node actions and help text; configuration values and service behavior preserved')
