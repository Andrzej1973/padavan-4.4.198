/* Included from rc/services.c only when APP_STUBBY is selected. */
int
is_stubby_run(void)
{
	return check_if_file_exist("/usr/sbin/stubby") && pids("stubby") != 0;
}

void
stop_stubby(void)
{
	if (eval("/usr/bin/stubby.sh", "stop") != 0)
		logmessage("Stubby", "Failed to stop service");
}

int
start_stubby(void)
{
	if (!get_ap_mode() && nvram_get_int("stubby_enable") == 1)
		return eval("/usr/bin/stubby.sh", "start");
	return 0;
}

void
restart_stubby(void)
{
	/* One helper invocation keeps stop/start under a single lifecycle lock. */
	if (!get_ap_mode() && nvram_get_int("stubby_enable") == 1) {
		if (eval("/usr/bin/stubby.sh", "restart") != 0)
			logmessage("Stubby", "Failed to restart service");
	} else {
		stop_stubby();
	}
}
