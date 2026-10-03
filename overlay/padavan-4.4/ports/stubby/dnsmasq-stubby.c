/* Included before start_dns_dhcpd in services_ex.c under APP_STUBBY. */
static int
stubby_dns_name_valid(const char *name)
{
	const unsigned char *p = (const unsigned char *)name;
	if (!name || strlen(name) < 3 || strlen(name) > 253)
		return 0;
	for (; *p; p++)
		if (!((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z') ||
		      (*p >= '0' && *p <= '9') || *p == '-' || *p == '.'))
			return 0;
	return 1;
}

static void
stubby_dnsmasq_config(FILE *fp)
{
	int mode = nvram_get_int("stubby_mode");
	int port = nvram_get_int("stubby_listen_port");
	int i;
	const char *listen_addr = "127.0.0.1";
	const char *value;
	char key[32], word[256], *next;
	char bootstrap_dns[16] = "";

	if (!nvram_match("stubby_enable", "1") || (mode != 1 && mode != 3))
		return;
	/* Never restore resolv-file because the daemon failed or settings are invalid. */
	fprintf(fp, "no-resolv\n");
	if (nvram_get_int("stubby_listen_mode") == 1)
		listen_addr = nvram_safe_get("lan_ipaddr_t");
	if (port >= 1 && port <= 65535 && is_valid_ipv4(listen_addr))
		fprintf(fp, "server=%s#%d\n", listen_addr, port);
	else
		logmessage("Stubby", "Invalid listener; ordinary upstream DNS remains disabled");

	/* Preserve the original, domain-scoped NTP bootstrap exception. */
	if (get_wan_dns_static()) {
		for (i = 1; i <= 3; i++) {
			snprintf(key, sizeof(key), "wan_dns%d_x", i);
			value = nvram_safe_get(key);
			if (is_valid_ipv4(value)) {
				snprintf(bootstrap_dns, sizeof(bootstrap_dns), "%s", value);
				break;
			}
		}
	} else {
		value = get_wan_unit_value(0, "dns");
		if (strlen(value) < 7)
			value = nvram_safe_get("wanx_dns");
		foreach(word, value, next) {
			if (is_valid_ipv4(word)) {
				snprintf(bootstrap_dns, sizeof(bootstrap_dns), "%s", word);
				break;
			}
		}
	}
	if (!is_valid_ipv4(bootstrap_dns))
		snprintf(bootstrap_dns, sizeof(bootstrap_dns), "%s", "8.8.8.8");
	for (i = 0; i < 2; i++) {
		snprintf(key, sizeof(key), "ntp_server%d", i);
		value = nvram_safe_get(key);
		if (stubby_dns_name_valid(value) && !is_valid_ipv4(value))
			fprintf(fp, "server=/%s/%s\n", value, bootstrap_dns);
	}
}
