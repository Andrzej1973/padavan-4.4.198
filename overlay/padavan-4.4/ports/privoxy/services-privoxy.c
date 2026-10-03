/* Included from rc/services.c when APP_PRIVOXY is selected. */
int
is_privoxy_run(void)
{
	return check_if_file_exist("/usr/sbin/privoxy") && pids("privoxy") != 0;
}

void
stop_privoxy(void)
{
	if (eval("/usr/bin/privoxy.sh", "stop") != 0)
		logmessage("Privoxy", "Failed to stop service");
}

void
start_privoxy(void)
{
	if (!get_ap_mode() && nvram_get_int("privoxy_enable") == 1)
		if (eval("/usr/bin/privoxy.sh", "start") != 0)
			logmessage("Privoxy", "Failed to start service");
}

void
restart_privoxy(void)
{
	if (!get_ap_mode() && nvram_get_int("privoxy_enable") == 1) {
		if (eval("/usr/bin/privoxy.sh", "restart") != 0)
			logmessage("Privoxy", "Failed to restart service");
	} else {
		stop_privoxy();
	}
}
