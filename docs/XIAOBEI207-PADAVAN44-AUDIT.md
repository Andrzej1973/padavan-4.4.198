# xiaobei207/padavan-4.4-2 — оцінка для нашого порту

Перевірено 2026-10-14. Репозиторій: [xiaobei207/padavan-4.4-2](https://github.com/xiaobei207/padavan-4.4-2).
Єдина гілка, повернута API: `main`, ревізія
`5e48032affbdf678d18ce7071e654f8dc0d61d68` (останній коміт main від 2025-07-24).
Поле pushed_at репозиторію — 2026-09-21; воно не означає новішого коду main.
Це форк TurBoTse/padavan. Порівняння з батьківською main
`c142aced25f7afc190cadb079d14b897c49c5b38` показало 55 комітів попереду,
84 позаду і 12 змінених шляхів від спільної бази. Це не повний diff між
кінцевими деревами і не порівняння з нашою прошивкою.

Наша база для предметного порівняння: vipshmily/padavan-4.4
`c25283e915a2a00a763774dd255b14aff997285e`, плюс власні накладки. Форк не
збирався і не запускався під час цього огляду. Пакети або драйвери не імпортовано.
Машинні ідентичності: [evidence/xiaobei207-review-20261014.json](evidence/xiaobei207-review-20261014.json).

## Кандидати для подальшої роботи

1. **MT76x2: захист читання файла.** У
   [rt_linux.c](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/os/linux/rt_linux.c)
   `RtmpOSFileRead()` перевіряє `osfd &&` перед `f_mode` у сучасній гілці.
   У закріпленій базі перевірки `osfd` тут немає. Кандидат на вузьке виправлення:
   перевірити також ERR_PTR, контракт викликів та нашу версію коду, потім
   компіляцію обох радіо. Зміна порога сумісності 3.19 → 4.1 для нашого 4.4.198
   сама по собі виграшу не доводить. Це не доказ виправлення HWNAT-зависання.
2. **WireGuard compat.**
   [version.h](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/linux-4.4.x/net/wireguard/version.h)
   містить `1.0.20220627`, наша база — `1.0.20210424`. Відрізняється не лише
   номер: allowedips, netlink, socket, receive/send і compatibility helpers.
   Кандидат на окреме зіставлення з офіційною історією upstream та тестування
   на kernel 4.4.198. Не замінювати ним AmneziaWG і не переносити сам version.h.
3. **Система пакетів.**
   [package.mk](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/include/package.mk)
   має окремі prepared/configured/built/installed stamps та прапорці LTO і
   gc-sections; download.mk передає hash до завантажувача.
   [msd_lite/Makefile](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/user/msd_lite/Makefile)
   закріплює Git commit `744d2ef91797471e26b3b117e7aa0ffebbb91106`.
   Корисний зразок для відтворюваних рецептів замість рухомого git clone.
   Повну систему rules.mk/include не переносити поверх наших Makefile без
   окремої міграції: змінені staging, шляхи та ABI toolchain.
4. **libxml2 з hash у рецепті.** Форк використовує 2.13.5 і заявлений SHA256
   `74fc163217a3964257d3be39af943e08861263c4231f9ef5b496b6f6d4c7b2b6`;
   наша база містить 2.13.3. Це кандидат для аудиту залежностей/джерел,
   не рекомендація обрати 2.13.5 як актуальну або безпечну версію сьогодні.
   Архів і hash незалежно не перевірялися.

## HWNAT, Wi-Fi й апаратна сумісність

Піддерева netfilter та shortcut-fe мають однакові Git tree SHA в обох базах.
Це не джерело нового fullcone/SFE виправлення у перевіреному зрізі.
Ethernet, vendor wireless, net/nat та WireGuard відрізняються; рекурсивні
переліки цих піддерев отримані без truncation.

У [ra_nat.c](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/linux-4.4.x/net/nat/hw_nat/ra_nat.c)
є `M2Q_table[skb->mark]` замість прямого qidx, інше multicast queue mapping,
і `ppe_set_entry_bind()` замість очищення FOE metadata. Це кандидат для
окремого аналізу QoS/HWNAT із перевіркою меж mark, конфігів та фактичного
вибору драйвера. Не називати готовим рішенням відомої проблеми Wi-Fi.

board.h, board.mk і l1profile.dat WR1200JS ідентичні нашій базі. kernel config
відрізняється: legacy HNAT/Wi-Fi offload, slab allocation і назва символу
`SECOND_IF_MT7612E` проти `RT_SECOND_IF_MT7612E`. Перенесення одного конфіга
без відповідних Kconfig/Makefile може мовчки вимкнути потрібне радіо.
Форк також видаляє багато старих файлів MT76x2; заміна всього каталогу
не є обґрунтованим способом порту.

WNM-зміни MT76x2 переводять printk на DBGPRINT, часто рівня ERROR/OFF.
Це не гарантує зменшення журналу й не замінює наш точковий Band Steering fix.
README перелічує WR1200JS, але фізичну працездатність цим не доведено.

## Що не переносити до поточного профілю

- Розгін NEWIFI3/XY-C1 до `0x372` (1120 МГц): інші плати, немає доказів
  температурної та навантажувальної стабільності нашого WR1200JS.
- [msd_lite.conf](https://github.com/xiaobei207/padavan-4.4-2/blob/5e48032affbdf678d18ce7071e654f8dc0d61d68/trunk/user/msd_lite/msd_lite.conf):
  precache 16384, ring 4096, socket buffers 2048, статичний vlan777 та info-log.
  Коментарі заявляють плавніше IPTV, але вимірів немає; precache більший за
  ring потребує перевірки семантики парсера. У нас MSD_LITE й UDPXY вимкнені.
- Workflow на checkout/setup/cache/upload `@main`, ubuntu-latest, watch/star
  trigger і автоматичне створення релізів. Наші контрольовані запуски,
  конфіг-перевірки й доказові артефакти зберегти. ccache уже працює в нашій CI.
- Заміна Git revision датою у versions.inc: втрачається однозначна ідентичність.
- Видалення частини авторів із footer: зберегти нашу атрибуцію.

## Висновок і межі огляду

Додати до джерел-кандидатів: MT76x2 file-read guard, WireGuard compat,
закріплені рецепти пакетів та окремий аналіз HWNAT queue/binding diff.
Нових власних виправлень Stubby/DoH, ZRAM або нашого клієнтського endpoint
у 12-шляховому diff форку від спільної бази не знайдено; це не повний аудит
усіх успадкованих служб. HTTPD має іншу структуру (`src/`), тож його виправлення
потребують окремого зіставлення. Працездатність форку не підтверджена тестами.
