#define BOARD_WR1200JS 1
#define WR_MODERN_HOST_TEST 1
#include <stdio.h>
#include <string.h>

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
	if (!strcmp(name, "rt_ssid")) return "Home-2.4G";
	if (!strcmp(name, "rt_channel")) return "6";
	if (!strcmp(name, "wl_ssid")) return "Home-5G";
	if (!strcmp(name, "wl_channel")) return "44";
	return "";
}

static int sysinfo(struct sysinfo *info)
{
	info->totalram = 262144;
	info->freeram = 131072;
	info->mem_unit = 4096;
	return 0;
}

static long uptime(void)
{
	return 301517;
}

#include "wr-modern-http.inc"

int main(void)
{
	do_wr_modern_json("", stdout);
	fputc('\n', stdout);
	return 0;
}
