# WR1200JS: вихід демона Band Steering без перезапуску — 2026-10-22

Read-only спостереження на живому пристрої та аналіз коду. Пристрій не
змінювався: без прошивки, перезавантаження, перезапуску демонів і запису NVRAM.

## Стан пристрою

- Прошивка `4.4.198.9`, ядро `#1 SMP Sun Oct 18 14:19:00 UTC 2026`, uptime
  4 дні 1:34.
- Тунель `wg1` живий (handshake < 2 хв), WAN `eth3` 5.58.139.185/18, LAN
  `br0` 192.168.20.1/24.
- Запущені: `httpd`, `dropbear`, `dnsmasq`, `stubby`. Не запущені:
  `iperf3`, `privoxy`, `xl2tpd`, `pptpd`, `wr-band-steering`.
- Пам'ять: 123 652 КБ всього, 47 268 КБ вільно. `/tmp` 23,8 МБ вільно.
- `/tmp/syslog.log` — 924 рядки за 4 доби; `dmesg` без error/fail/oops/panic.
- Сторінка VPN-профілів присутня: `/www/vpncli.asp` 113 222 байт,
  містить `wr_vpn_profile_rows`, `WRVPN_PROFILES_TITLE`, `wr_vpn_action.cgi`;
  `httpd` містить обробник. Це підтверджує, що виправлення `03eb3da` вже
  працює в полі.

## Band Steering

NVRAM:

| Ключ | Значення |
| --- | --- |
| `wr_bs_enable` | 1 |
| `wr_bs_apply_state` | 5 (`WR_APPLY_RUNNING`) |
| `wr_bs_off_confirmed` | 0 |
| `wr_bs_boot_profiles_ready` | 1 |

Факти:

- Демон `wr-band-steering` не запущений (`pidof` порожній).
- `wr-band-steering-ctl status` → `Control endpoint unavailable or invalid;
  radio state unverified`.
- Ядро о `18:53:49` записало `BndStrg_Enable(): Band steering stop running.`
- Каталог `/var/run/wr-band-steering/` спорожнів о 18:53 (mtime), lock-файл
  датований 19.10 21:30 — тобто демон пропрацював близько трьох діб.
- У syslog немає жодного рядка `Band Steering` (ані `start`, ані
  `Owned daemon exited`).

Висновок: стан `WR_APPLY_RUNNING` застарілий — NVRAM стверджує роботу, якої
немає. Це окремий дефект спостережуваності, незалежно від причини смерті
процесу.

## Код

- `tools/band-steering/loop.c`: у циклі приймання будь-яка помилка, крім
  `EAGAIN`/`EWOULDBLOCK`/`EINTR`, викликає `fault()` і завершує демон. Коментар
  у коді прямо згадує `ENOBUFS` і пошкоджені/обрізані події ядра.
- `tools/band-steering/main.c`: `wait_events()` повертає `-1` на
  `POLLERR`/`POLLHUP`/`POLLNVAL`; `main()` у будь-якому такому разі йде в
  `done` і завершується з `result = 1`.
- Автоматичного перезапуску немає: `rc` має `restart_wr_band_steering`, але
  викликає його на зміну налаштувань, а не як watchdog після аварійного виходу.
- `tools/band-steering/prepare-wifi-lifecycle.py` містить
  `wr_band_wifi_child_exit()` і запис
  `Owned daemon exited: clean=... exit=... signal=...`, але на пристрої такого
  рядка немає. Або збірка від 18.10 старіша за цей код, або шлях обробки
  SIGCHLD не спрацював.

## Статуси

| Елемент | Стан |
| --- | --- |
| Демон Band Steering на пристрої | не працює (факт) |
| Автоматичний перезапуск після аварії | не реалізовано |
| Оновлення NVRAM-стану після смерті демона | дефект: стан застарілий |
| Логування причини виходу на пристрої | не підтверджено |
| Точний errno смерті | не встановлено (stderr не збережено) |

## Наступні кроки

1. Зберегти stderr демона у файл або syslog, щоб отримати `exit`/`signal` і
   причину.
2. Додати supervisor з backoff: аварійний вихід → повторний запуск через
   `rc`-узгодження профілів, а не сліпий рестарт.
3. Оновлювати `wr_bs_apply_state` на `WR_APPLY_START_ERROR`/`OFF_UNVERIFIED`
   при смерті демона, щоб WebUI не показував хибне «працює».
4. Розглянути окремо: чи `ENOBUFS` від netlink має бути відновлюваним
   (дренування черги), чи це має лишатися fatal із зовнішнім перезапуском.

Жоден із пунктів не виконано; рішення про перезапуск демона на пристрої
залишається за користувачем.
