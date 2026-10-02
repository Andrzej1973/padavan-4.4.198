/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Preserve the source firmware's VPN lifecycle and interface names. */
#include "rc.h"

int start_wireguard_client(void)
{
	int ret;
	nvram_set_temp("wg_log_reduce_t", "");
	ret = eval("/usr/bin/wgc.sh", "start");
	if (ret == 0)
		set_vpn_balancing("wg0", 0);
	return ret;
}

void stop_wireguard_client(void)
{
	eval("/usr/bin/wgc.sh", "stop");
}

int start_wireguard_server(void)
{
	int ret = eval("/usr/bin/wgs.sh", "start");
	if (ret == 0)
		set_vpn_balancing("wg1", 1);
	return ret;
}

void stop_wireguard_server(void)
{
	eval("/usr/bin/wgs.sh", "stop");
}

void restart_wireguard_server(void)
{
	eval("/usr/bin/wgs.sh", "restart");
}
