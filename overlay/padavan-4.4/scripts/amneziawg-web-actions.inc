#if defined(APP_AMNEZIAWG)
	else if (!strcmp(value, " wg_action "))
	{
		FILE *fp;
		char command[256], result[256] = {0};
		char *action = websGetVar(wp, "action", "");
		char *privkey = websGetVar(wp, "privkey", "");
		int status;
		if (!get_login_safe())
			return 0;
		if (!strcmp(action, "genkey"))
			snprintf(command, sizeof(command), "/usr/bin/awg genkey");
		else if (!strcmp(action, "genpsk"))
			snprintf(command, sizeof(command), "/usr/bin/awg genpsk");
		else if (!strcmp(action, "pubkey")) {
			/* A WG key is 43 base64 characters followed by '='.
			 * Validate before including it in the fixed shell command. */
			if (strlen(privkey) != 44 || privkey[43] != '=' ||
			    strspn(privkey, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") != 43)
				return 0;
			snprintf(command, sizeof(command),
				 "printf '%%s\\n' '%s' | /usr/bin/awg pubkey", privkey);
		} else
			return 0;
		fp = popen(command, "r");
		if (!fp)
			return 0;
		if (!fgets(result, sizeof(result), fp))
			result[0] = '\0';
		status = pclose(fp);
		result[strcspn(result, "\r\n")] = '\0';
		if (status == 0 && strlen(result) == 44 && result[43] == '=' &&
		    strspn(result, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") == 43)
			websWrite(wp, "%s", result);
		return 0;
	}
	else if (!strcmp(value, " ExportWGConf "))
	{
		char *common_name = websGetVar(wp, "common_name", "");
		if (!get_login_safe() || !*common_name)
			return 0;
		/* Pass the name as an argv element, and never serve stale output. */
		unlink("/tmp/client-wg.conf");
		if (eval("/usr/bin/wgs.sh", "export", common_name) == 0)
			do_file("/tmp/client-wg.conf", wp);
		unlink("/tmp/client-wg.conf");
		return 0;
	}
#endif
