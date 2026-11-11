# WebUI — збережений стан і призупинення

Власник призупинив усю роботу над WebUI 2026-11-11 до окремої прямої вказівки.
Збережено вихідний код, модель налаштувань, backend-кандидати, тести, ТЗ, еталони
та результати перевірок. IoT і мережева робота продовжуються за чинним пріоритетом.

## Покажчик матеріалів

| Матеріали | Розташування |
|---|---|
| HTML/CSS/JS, DEMO, production shell, проєкція збережених параметрів | [tools/webui-preview](../../tools/webui-preview/README.md) |
| Спільна логіка Wi-Fi й інтеграція з Padavan | [tools/shared-wifi](../../tools/shared-wifi) та [prepare-shared-wifi.py](../../tools/prepare-shared-wifi.py) |
| Поточні стани й межі Apply | [Wi-Fi apply contract](../WR1200JS-MODERN-WIFI-APPLY-CONTRACT.md) |
| Повне покриття сторінок і підсторінок | [Page coverage](../WR1200JS-MODERN-PAGE-COVERAGE.md), [page map](../WR1200JS-MODERN-PAGE-MAP.json) |
| Поля та конфігураційні поверхні Classic | [Config inventory](../WEBUI-CONFIG-INVENTORY.csv), [coverage inventory](../WEBUI-COVERAGE-INVENTORY.json) |
| ТЗ прийнятих макетів | [01 — спільні](../modern-design/01-WIFI-COMMON-UK.md), [02 — 2,4 ГГц](../modern-design/02-WIFI-24-GENERAL-UK.md), [03 — Guest 2,4](../modern-design/03-WIFI-24-GUEST-UK.md), [04 — 5 ГГц](../modern-design/04-WIFI-5-GENERAL-UK.md) |
| Візуальні джерела з початковими назвами та SHA256 | [25 записів, 24 унікальні PNG](../modern-design/references/README.md) |
| Початковий план власника | [Development plan](reference/PADAVAN_4.4.198_Development_Plan_EN.txt) |
| Фінальні варіанти релізу та порівняння розмірів TRX | [Modern + Classic / Modern only](../WR1200JS-FINAL-WEBUI-RELEASE-VARIANTS.md) |
| Точний перелік збережених файлів і контрольні суми | [checkpoint.json](checkpoint.json) |

## Стан реалізації

Сторінки01–04 мають прийняті ТЗ та збережені макети. Production shell показує
збережені параметри Wi-Fi й Guest, обидва діапазони, спільний режим та розклад.
Сторінка IoT зарезервована зі статусом розробки. Повний обсяг охоплює всі
погоджені сторінки, підсторінки й діалоги. Решта сторінок потребує індивідуальної
реалізації та приймання за page map.

Backend-кандидати збережені в tools/webui-preview разом із генераторами
ізольованого HTTP, CGI-валідацією, keep/change для пароля, Guest-планувальником,
атомарним NVRAM batch ioctl і перевірками commit/notify. Production Apply
очікує завершення інтеграції та перевірок. Чернетка перевірки радіопараметрів
2,4 ГГц містить trusted HT40 mask. Її policy provider та повна серіалізація
читачів і всіх writer-шляхів залишаються відкритими задачами.

Локальні channel-list/RTNL дослідження, HT40-правки й історичні докази CI998,
CI999 та CI1000–1002 включено в цей checkpoint. Їхній статус визначають записані
scope та revision. Актуальніші докази — [CI1004–1005](../evidence/WR1200JS-MODERN-CI1004-1005-CHECKPOINT-2026-11-11.md),
[page04 browser](../evidence/WR1200JS-MODERN-PAGE04-BROWSER-2026-11-11.json)
і [batch CGI](../evidence/WR1200JS-MODERN-BATCH-CGI-HOST-2026-11-11.json).

Під час збереження повторно пройшли check_json.py з ASan/UBSan та
check_wifi_production.js для15 production Wi-Fi routes. Нових фізичних
перевірок WebUI в цьому checkpoint немає. Значення на малюнках залишаються
візуальними прикладами. Цей checkpoint охоплює вихідний код і модель налаштувань веб-UI.

## Відновлення роботи після вказівки власника

1. Прочитати цей покажчик, checkpoint.json, PROJECT_STATUS.md та CODEX_HANDOFF.md.
2. Звірити branch/HEAD, робочу копію та потрібні результати CI.
3. Повернутися до незавершеної інтеграції збереження налаштувань і приймання
   поточних сторінок, використовуючи чинні CGI/NVRAM/RC-шляхи й джерела SDK.
4. Для нової сторінки погодити її ТЗ та дочекатися готового макета від власника.
5. Завершити обидва варіанти релізу з однаковими вхідними даними збірки та
   виміряти їхні фактичні стиснені TRX і SHA256.

PNG-еталони займають26173588 байтів, приблизно25 MiB. Це збережені вхідні
матеріали дизайну. Дубль зображення посилається на ту саму копію в manifest.
