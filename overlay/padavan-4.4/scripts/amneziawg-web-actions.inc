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
		char directory[] = "/tmp/wr-vpn-export-XXXXXX";
		char path[sizeof(directory) + sizeof("/client.conf")];
		if (!get_login_safe() || !*common_name)
			return 0;
		if (!mkdtemp(directory))
			return 0;
		snprintf(path, sizeof(path), "%s/client.conf", directory);
		if (eval("/usr/bin/wgs.sh", "export", common_name, path) == 0)
			do_file(path, wp);
		unlink(path);
		rmdir(directory);
		return 0;
	}
#endif
