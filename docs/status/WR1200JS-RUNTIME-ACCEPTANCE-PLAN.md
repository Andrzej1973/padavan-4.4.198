# WR1200JS — протокол runtime-приймання

Використовувати лише після **окремого дозволу власника** на прошивку. Сам
документ не дає дозволу на flash, reboot або зміну налаштувань.

## Передумови

1. Є зелений CI-образ і його SHA256 (наприклад, build #533:
   `f096e4f5b30d836d2cd57c2242ffb7cfacdef8cf6182206494ef623be71d0d4d`).
2. Є приватний бекап EEPROM/Config:
   `router-backups/2026-10-22/` (Factory `mtd2`, Config `mtd1`).
3. Є експорт поточних налаштувань через WebUI (файл зберігати приватно).
4. Є доступ по SSH і через тунель; відомо, як підняти тунель, якщо він
   відпаде.
5. Підтверджено, що новий образ не змінює пароль/ключі доступу.

## Після прошивки — read-only перевірки (у цьому порядку)

| # | Перевірка | Команда / місце | Критерій |
| --- | --- | --- | --- |
| 1 | Пристрій піднявся | `uptime`, `nvram get firmver` | uptime зростає, версія очікувана |
| 2 | SSH живий | повторний вхід | вхід без помилок |
| 3 | LAN | `ip -4 addr show br0` | 192.168.20.1/24 |
| 4 | Тунель | `wg show wg1` | interface є, handshake < 3 хв |
| 5 | WebUI через LAN | `curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://192.168.20.1/` | 401 (сторінка жива, потрібен логін) |
| 6 | WebUI через тунель | те саме на 192.168.30.1 | 401 |
| 7 | DNS | `nslookup openwrt.org 127.0.0.1` | відповідь з адресами |
| 8 | Інтернет | `ping -c 2 1.1.1.1` | 0% втрат |
| 9 | VPN-профілі | `grep -c wr_vpn_profile_rows /www/vpncli.asp` | ≥1 |
| 10 | Band Steering: демон | `pidof wr-band-steering` | PID є |
| 11 | Band Steering: стан | `wr-band-steering-ctl status` | не `Control endpoint unavailable` |
| 12 | Band Steering: діагностика | `grep -E 'band-steering (loop fault|poll failure)' /tmp/syslog.log` | рядків немає (якщо є — зафіксувати) |
| 13 | Шум Band Steering | `grep -c -E 'BndStrg|Reaped' /tmp/syslog.log` | без періодичного спаму |
| 14 | CAKE | `ls /lib/modules/4.4.198 | grep -c cake` | 0 |
| 15 | Сервіси | `pidof httpd dropbear dnsmasq stubby` | усі мають PID |
| 16 | Помилки ядра | `dmesg`, пошук oops/panic/call trace | 0 збігів |
| 17 | Пам'ять | `free` | вільно > 20 МБ після 10 хв |
| 18 | Налаштування | `/www/Advanced_SettingBackup_Content.asp` доступна; `mtd_storage.sh` є | є |

## Критерії приймання

- Усі пункти 1–8 виконані (доступ не втрачено).
- Пункт 10–11: демон живий, endpoint доступний.
- Немає reboot-loop і немає `oops/panic/call trace`.
- Будь-який невдалий пункт фіксується як дефект; успішний CI не підміняє
  runtime-результат.

## Якщо щось пішло не так

1. Не робити повторних перезавантажень «на удачу».
2. Зберегти `/tmp/syslog.log` (приватно) і `dmesg` для розбору.
3. Відновити налаштування з приватного експорту; EEPROM/Config не чіпати без
   окремого рішення.
4. Повернутися до попереднього образу лише за окремим дозволом.
