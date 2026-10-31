#if defined(BOARD_WR1200JS)
static void wr_modern_json_string(FILE *stream, const char *value)
{
	const unsigned char *cursor = (const unsigned char *)(value && *value ? value : "N/A");

	fputc('"', stream);
	while (*cursor) {
		switch (*cursor) {
		case '"': fputs("\\\"", stream); break;
		case '\\': fputs("\\\\", stream); break;
		case '\b': fputs("\\b", stream); break;
		case '\f': fputs("\\f", stream); break;
		case '\n': fputs("\\n", stream); break;
		case '\r': fputs("\\r", stream); break;
		case '\t': fputs("\\t", stream); break;
		default:
			if (*cursor < 0x20)
				fprintf(stream, "\\u%04x", *cursor);
			else
				fputc(*cursor, stream);
		}
		cursor++;
	}
	fputc('"', stream);
}

static const char *wr_modern_nvram(const char *name)
{
	const char *value = nvram_safe_get(name);
	return (value && *value) ? value : "N/A";
}

static void wr_modern_json_field(FILE *stream, const char *name,
	const char *value, int comma)
{
	wr_modern_json_string(stream, name);
	fputc(':', stream);
	wr_modern_json_string(stream, value);
	if (comma)
		fputc(',', stream);
}

static void do_wr_modern_json(const char *url, FILE *stream)
{
	struct sysinfo info;
	char uptime_text[64];
	char firmware[64];
	unsigned long uptime_seconds = (unsigned long)uptime();
	unsigned long long memory_total = 0;
	unsigned long long memory_free = 0;
	unsigned int memory_percent = 0;
	unsigned int hours, minutes, seconds, days;
	const char *wan_ip;
	(void)url;

	hours = uptime_seconds / 3600UL;
	days = hours / 24U;
	hours %= 24U;
	minutes = (uptime_seconds / 60UL) % 60UL;
	seconds = uptime_seconds % 60UL;
	snprintf(uptime_text, sizeof(uptime_text), "%u д %02u:%02u:%02u",
		days, hours, minutes, seconds);
	snprintf(firmware, sizeof(firmware), "%s/%s",
		wr_modern_nvram("firmver"), wr_modern_nvram("extendno"));
	if (sysinfo(&info) == 0) {
		memory_total = (unsigned long long)info.totalram * info.mem_unit;
		memory_free = (unsigned long long)info.freeram * info.mem_unit;
		if (memory_total)
			memory_percent = (unsigned int)(((memory_total - memory_free) * 100ULL) / memory_total);
	}
	wan_ip = wr_modern_nvram("wan0_ipaddr");

	fputs("{\"demo\":false,", stream);
	wr_modern_json_field(stream, "device", wr_modern_nvram("productid"), 1);
	wr_modern_json_field(stream, "firmware", firmware, 1);
	fputs("\"internet\":{", stream);
	wr_modern_json_field(stream, "status",
		strcmp(wan_ip, "N/A") != 0 && strcmp(wan_ip, "0.0.0.0") != 0
			? "Підключено" : "Н/Д", 1);
	wr_modern_json_field(stream, "connection", wr_modern_nvram("wan0_proto"), 1);
	wr_modern_json_field(stream, "ip", wan_ip, 1);
	wr_modern_json_field(stream, "uptime", uptime_text, 0);
	fputs("},\"wifi\":[", stream);
	fputs("{\"band\":\"2,4 ГГц\",\"status\":\"Налаштовано\",", stream);
	wr_modern_json_field(stream, "ssid", wr_modern_nvram("rt_ssid"), 1);
	wr_modern_json_field(stream, "channel", wr_modern_nvram("rt_channel"), 1);
	fputs("\"speed\":\"Н/Д\",\"clients\":\"Н/Д\"},", stream);
	fputs("{\"band\":\"5 ГГц\",\"status\":\"Налаштовано\",", stream);
	wr_modern_json_field(stream, "ssid", wr_modern_nvram("wl_ssid"), 1);
	wr_modern_json_field(stream, "channel", wr_modern_nvram("wl_channel"), 1);
	fputs("\"speed\":\"Н/Д\",\"clients\":\"Н/Д\"}],", stream);
	fputs("\"devices\":{\"total\":\"Н/Д\",\"wired\":\"Н/Д\",\"wifi24\":\"Н/Д\",\"wifi5\":\"Н/Д\"},", stream);
	fputs("\"cpuPercent\":null,", stream);
	fprintf(stream, "\"memoryPercent\":%u,", memory_percent);
	fputs("\"zram\":{\"status\":\"Н/Д\",\"used\":\"Н/Д\",\"compression\":\"Н/Д\",\"percent\":null},", stream);
	fputs("\"usb\":{\"status\":\"Н/Д\",\"filesystem\":\"Н/Д\",\"freeTotal\":\"Н/Д\"},", stream);
	fputs("\"interfaces\":{\"status\":\"WAN/LAN з NVRAM\",\"detail\":\"Runtime-перевірка не виконувалась\"},", stream);
	wr_modern_json_field(stream, "uptime", uptime_text, 1);
	fputs("\"iot\":{\"status\":\"Не підтверджено\",\"detail\":\"Production IoT runtime ще не прийнято\"},", stream);
	fputs("\"temperatures\":{\"cpu\":null,\"radio5\":null,\"note\":\"Н/Д\"},", stream);
	fputs("\"traffic\":{\"download\":null,\"upload\":null,\"samples\":[]},", stream);
	fputs("\"processes\":[],\"pages\":{", stream);

	fputs("\"internet\":{\"title\":\"Інтернет (WAN)\",\"classic\":\"Advanced_WAN_Content.asp\","
		"\"description\":\"Поточні read-only значення NVRAM.\",\"fields\":[", stream);
	fputs("{\"label\":\"Тип підключення\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("wan0_proto"));
	fputs("},{\"label\":\"IP-адреса\",\"value\":", stream);
	wr_modern_json_string(stream, wan_ip);
	fputs("},{\"label\":\"MTU\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("wan0_mtu"));
	fputs("}]},", stream);

	fputs("\"iot\":{\"title\":\"Мережа IoT\",\"classic\":\"Advanced_Wireless2g_Content.asp\","
		"\"description\":\"Production IoT lifecycle не прийнятий.\",\"fields\":["
		"{\"label\":\"Стан\",\"value\":\"Не підтверджено\"},"
		"{\"label\":\"Ізоляція LAN\",\"value\":\"Не підтверджено\"}]},", stream);

	fputs("\"lan\":{\"title\":\"Локальна мережа (LAN)\",\"classic\":\"Advanced_APLAN_Content.asp\","
		"\"description\":\"Поточні read-only значення NVRAM.\",\"fields\":[", stream);
	fputs("{\"label\":\"IP-адреса роутера\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("lan_ipaddr"));
	fputs("},{\"label\":\"Маска підмережі\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("lan_netmask"));
	fputs("},{\"label\":\"Початок DHCP\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("dhcp_start"));
	fputs("},{\"label\":\"Кінець DHCP\",\"value\":", stream);
	wr_modern_json_string(stream, wr_modern_nvram("dhcp_end"));
	fputs("}]},", stream);

	fputs("\"vpn\":{\"title\":\"VPN\",\"classic\":\"vpncli.asp / Advanced_zerotier.asp\","
		"\"description\":\"Керування виконується лише у Classic.\",\"services\":["
		"{\"name\":\"WireGuard\",\"state\":\"Classic\"},"
		"{\"name\":\"AmneziaWG\",\"state\":\"Classic\"},"
		"{\"name\":\"ZeroTier\",\"state\":\"Classic\"},"
		"{\"name\":\"Shadowsocks\",\"state\":\"Classic\"}]},", stream);
	fputs("\"dns\":{\"title\":\"DNS і проксі\",\"classic\":\"Advanced_DHCP_Content.asp / Advanced_Services_Content.asp\","
		"\"description\":\"Стани DNS-служб не перевіряються цим endpoint.\",\"services\":["
		"{\"name\":\"Stubby\",\"state\":\"Classic\"},"
		"{\"name\":\"DoH\",\"state\":\"Classic\"},"
		"{\"name\":\"Privoxy\",\"state\":\"Classic\"},"
		"{\"name\":\"WPAD / PAC\",\"state\":\"Classic\"}]},", stream);
	fputs("\"services\":{\"title\":\"Служби\",\"classic\":\"Advanced_Services_Content.asp\","
		"\"description\":\"Керування службами залишається у Classic.\",\"services\":["
		"{\"name\":\"SSH\",\"state\":\"Classic\"},"
		"{\"name\":\"iPerf3\",\"state\":\"Classic\"},"
		"{\"name\":\"Cron\",\"state\":\"Classic\"},"
		"{\"name\":\"Watchdog\",\"state\":\"Classic\"},"
		"{\"name\":\"Виявлення пристроїв\",\"state\":\"Classic\"}]},", stream);
	fputs("\"monitoring\":{\"title\":\"Моніторинг\",\"classic\":\"Main_LogStatus_Content.asp\","
		"\"description\":\"Доступні лише перевірені системні значення.\",\"fields\":["
		"{\"label\":\"Використання пам’яті\",\"value\":\"", stream);
	fprintf(stream, "%u%%", memory_percent);
	fputs("\"},{\"label\":\"Температура CPU\",\"value\":\"Н/Д\"},"
		"{\"label\":\"Температура Wi-Fi 5 ГГц\",\"value\":\"Н/Д\"}]},", stream);
	fputs("\"system\":{\"title\":\"Система\",\"classic\":\"Advanced_System_Content.asp\","
		"\"description\":\"Read-only системні значення.\",\"fields\":["
		"{\"label\":\"Версія прошивки\",\"value\":", stream);
	wr_modern_json_string(stream, firmware);
	fputs("},{\"label\":\"Час роботи\",\"value\":", stream);
	wr_modern_json_string(stream, uptime_text);
	fputs("}]},", stream);
	fputs("\"log\":{\"title\":\"Журнал\",\"classic\":\"Main_LogStatus_Content.asp\","
		"\"description\":\"Журнал не дублюється у Modern endpoint.\",\"log\":[\"Відкрийте журнал у Padavan Classic\"]},", stream);
	fputs("\"firewall\":{\"title\":\"Брандмауер\",\"classic\":\"Advanced_Firewall_Content.asp\","
		"\"description\":\"Правила змінюються лише у Classic.\",\"fields\":["
		"{\"label\":\"Runtime\",\"value\":\"Не перевірено\"}]},", stream);
	fputs("\"qos\":{\"title\":\"QoS\",\"classic\":\"Advanced_SQM.asp\","
		"\"description\":\"CAKE виключений вимогою проєкту.\",\"fields\":["
		"{\"label\":\"CAKE\",\"value\":\"Виключено\"},"
		"{\"label\":\"Runtime\",\"value\":\"Не перевірено\"}]}},", stream);

	fputs("\"serviceTiles\":[", stream);
	{
		static const char *names[] = {
			"Stubby", "DoH", "WireGuard", "AmneziaWG", "ZeroTier",
			"Shadowsocks", "Privoxy", "WPAD / PAC", "HTTP / HTTPS", "SSH",
			"iPerf3", "Cron", "KMS", "Zapret2"
		};
		static const char *details[] = {
			"DNS-over-TLS", "DNS-over-HTTPS", "VPN", "VPN", "SD-WAN",
			"Proxy / VPN", "Веб-фільтр", "Автонастроювання", "WebUI", "SSH",
			"LAN speed", "Scheduler", "KMS", "nfqws2"
		};
		static const char *icons[] = {
			"check", "globe", "shield", "shield", "gear",
			"share", "file", "server", "globe", "cube",
			"gear", "server", "check", "shield"
		};
		unsigned int index;
		for (index = 0; index < sizeof(names) / sizeof(names[0]); index++) {
			if (index)
				fputc(',', stream);
			fputs("{\"name\":", stream);
			wr_modern_json_string(stream, names[index]);
			fputs(",\"detail\":", stream);
			wr_modern_json_string(stream, details[index]);
			fputs(",\"icon\":", stream);
			wr_modern_json_string(stream, icons[index]);
			fputs(",\"href\":\"Advanced_Services_Content.asp\",\"availableInBuild\":true,\"runtimeVerified\":false}", stream);
		}
	}
	fputs("],\"classicPages\":[]}", stream);
}
#endif
