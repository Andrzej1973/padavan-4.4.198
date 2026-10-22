# WR1200JS — матриця станів, 2026-10-22

Скорочений, доказовий зріз. Кожен рядок посилається на артефакт або
evidence-файл; успішна збірка не означає успішного порту на пристрої.

| Функція | Стан | Доказ / межа |
| --- | --- | --- |
| Прошивка збирається | перевірено успішно | build #533, `c8bce32`; TRX 12 843 785 Б, SHA256 `f096e4f5…0d4d`; усі uImage-перевірки `true` |
| Образ містить VPN-профілі | перевірено успішно (образ) | `/www/vpncli.asp` — `wr_vpn_profile_rows` ×2; `httpd` — обробники; UK/EN підписи |
| Робота VPN-профілів на пристрої | частково перевірено | на пристрої (збірка 18.10) сторінка й обробники є; список профілів порожній; живий тунель `wg1` |
| Band Steering: шум у логах | перевірено успішно | 12 рядків за 4 доби, усі при старті |
| Band Steering: живучість демона | не реалізовано | демон помер 22.10 18:53:49; `wr_bs_apply_state=5` застарілий; recovery/resync відсутній |
| Band Steering: діагностика причини | перевірено успішно (образ) | `wr-band-steering` містить `band-steering loop fault` і `poll failure`; на пристрої `/dev/log` + syslogd є |
| Band Steering: звіт про вихід після втрати owner | перевірено успішно (host) | ABI #504, крок `Verify actual rc Wi-Fi lifecycle callbacks` |
| Band Steering: supervised re-arm | проєкт | `docs/BAND-STEERING-SUPERVISION.md`; не реалізовано |
| CAKE | перевірено успішно (відсутній) | `sch_cake.ko` немає; `CONFIG_FIRMWARE_INCLUDE_SQM` не встановлено |
| Wi-Fi інваріанти | частково перевірено | NVRAM: `rt_HT_AMSDU=0`, `rt_ldpc=0`, `wl_ldpc=0`, `hw_nat_mode=2`; `wl_mumimo`/greenfield unset → 0; драйверний стан не читається |
| Beamforming 5 ГГц | заблоковано природно | `CONFIG_MT76X2_AP_TXBF_SUPPORT` не ввімкнено; Factory `0x01A0`/`0x81A0` — 33/33 байти `0xFF` (немає калібровки); `wl_txbf_en=0` |
| Сервіси DoH/Stubby/Privoxy/iPerf3 | перевірено успішно (пакування) | відповідні `*-image-checks.json` без `false`; runtime не перевірено |
| Резервне копіювання налаштувань | перевірено успішно (наявність) | сторінка є; `restore_nv.cgi`/`restore_st.cgi`/`apply.cgi` у `httpd`; `mtd_storage.sh` є |
| EoIP / OpenVPN / PPTP / L2TP | перевірено успішно (виключені) | `eoip-image-checks.json`: `feature_selected=false`; у посібнику 0 згадок |
| IoT | частково реалізовано | кандидатні гейти в ABI #504 зелені; у production-образі `wr-iot*` немає; transition owner не реалізовано |
| Mi Mini | не розпочато | наступний етап після WR1200JS |
| Черга CI | виправлено локально | `9c56b39`: `firmware-<ref>`, `abi-<ref>`, monitor `cancel-in-progress`; правило в `AGENTS.md` |
| Пристрій | не прийнято | працює збірка від 18.10; нові образи не встановлювались |
