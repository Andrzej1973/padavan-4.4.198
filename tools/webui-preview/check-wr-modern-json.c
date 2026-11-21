#define BOARD_WR1200JS 1
#define WR_MODERN_HOST_TEST 1
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static const char *ssid_override;

struct sysinfo {
	unsigned long totalram;
	unsigned long freeram;
	unsigned int mem_unit;
};

static const char *nvram_safe_get(const char *name)
{
	if (!strcmp(name, "productid")) return "WR1200JS";
	if (!strcmp(name, "firmver")) return "4.4.198.9";
	if (!strcmp(name, "extendno")) return "WR1200JS";
	if (!strcmp(name, "wan0_proto")) return "pppoe";
	if (!strcmp(name, "wan0_ipaddr")) return "192.0.2.10";
	if (!strcmp(name, "wan0_mtu")) return "1492";
	if (!strcmp(name, "lan_ipaddr")) return "192.168.1.1";
	if (!strcmp(name, "lan_netmask")) return "255.255.255.0";
	if (!strcmp(name, "dhcp_start")) return "192.168.1.100";
	if (!strcmp(name, "dhcp_end")) return "192.168.1.200";
	if (!strcmp(name, "rt_ssid")) return ssid_override ? ssid_override : "Home-2.4G";
	if (!strcmp(name, "rt_channel")) return "6";
	if (!strcmp(name, "wl_ssid")) return "Home-5G";
	if (!strcmp(name, "wl_channel")) return "44";
	if (!strcmp(name, "wr_wifi_shared")) return "0";
	if (!strcmp(name, "rt_auth_mode") || !strcmp(name, "wl_auth_mode")) return "psk";
	if (!strcmp(name, "rt_wep_x") || !strcmp(name, "wl_wep_x")) return "0";
	if (!strcmp(name, "rt_wpa_mode") || !strcmp(name, "wl_wpa_mode")) return "2";
	if (!strcmp(name, "rt_crypto") || !strcmp(name, "wl_crypto")) return "aes";
	if (!strcmp(name, "rt_radio_x") || !strcmp(name, "wl_radio_x")) return "1";
	if (!strcmp(name, "rt_closed") || !strcmp(name, "wl_closed")) return "0";
	if (!strcmp(name, "rt_HT_BW") || !strcmp(name, "wl_HT_BW")) return "1";
	if (!strcmp(name, "rt_gmode") || !strcmp(name, "wl_gmode")) return "2";
	if (!strcmp(name, "rt_HT_EXTCHA") || !strcmp(name, "wl_HT_EXTCHA")) return "1";
	if (!strcmp(name,"rt_country_code") || !strcmp(name,"wl_country_code")) return "UA";
	if (!strcmp(name,"rt_radio_date_x") || !strcmp(name,"wl_radio_date_x")) return "0111110";
	if (!strcmp(name,"rt_radio_time_x") || !strcmp(name,"wl_radio_time_x")) return "08002200";
	if (!strcmp(name,"rt_radio_time2_x") || !strcmp(name,"wl_radio_time2_x")) return "10002300";
	if (!strncmp(name, "rt_guest_", 9) || !strncmp(name, "wl_guest_", 9)) {
		const char *field = name + 9;
		if (!strcmp(field, "ssid")) return name[0] == 'r' ? "Guest-24" : "Guest-5";
		if (!strcmp(field, "auth_mode")) return "psk";
		if (!strcmp(field, "wpa_mode")) return "2";
		if (!strcmp(field, "crypto")) return "aes";
		if (!strcmp(field, "date_x")) return "0111110";
		if (!strcmp(field, "time_x")) return "08002200";
		if (!strcmp(field, "time2_x")) return "10002300";
		if (!strcmp(field, "enable") || !strcmp(field, "lan_isolate") || !strcmp(field, "ap_isolate")) return "1";
		if (!strcmp(field, "closed") || !strcmp(field, "macrule") || !strcmp(field, "mcs_mode")) return "0";
	}
	fprintf(stderr, "Unexpected NVRAM read: %s\n", name);
	exit(2);
}

static int memory_case;

static int sysinfo(struct sysinfo *info)
{
	info->totalram = 262144;
	info->freeram = 131072;
	info->mem_unit = 4096;
	if (memory_case == 1) return -1;
	if (memory_case == 2) info->totalram = 0;
	if (memory_case == 3) info->freeram = info->totalram + 1;
	return 0;
}

static long uptime(void)
{
	return 301517;
}

#include "wr-modern-http.inc"

int main(int argc, char **argv)
{
	if (argc > 1) memory_case = argv[1][0] - '0';
	if (argc > 2) ssid_override = argv[2];
	do_wr_modern_json("", stdout);
	fputc('\n', stdout);
	return 0;
}
