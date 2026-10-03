#if defined(APP_AMNEZIAWG)
#define VPN_SERVER_LEASE_FILE "/tmp/vpns.leases"
#define MAX_CLIENTS_NUM (50)
void
leases_wireguard_server(void)
{
    if (nvram_get_int("vpns_enable") == 0 || nvram_get_int("vpns_type") != 3)
        return;

    FILE *fp, *fp_leases;
    char command[256], result[2048];

    if ((fp_leases = fopen(VPN_SERVER_LEASE_FILE, "w")) == NULL) {
        return;
    }

    int clients_count = nvram_get_int("vpns_num_x");
    if (clients_count > MAX_CLIENTS_NUM) {
        clients_count = MAX_CLIENTS_NUM;
    }

    snprintf(command, sizeof(command), "/usr/sbin/wg show '%s' dump", "wg1");
    if ((fp = popen(command, "r")) == NULL) {
        fclose(fp_leases);
        return;
    }

    while (fgets(result, sizeof(result), fp)) {
        for (int i = 0; i < clients_count; i++) {
            char acl_user_var[32], acl_public_var[44];
            snprintf(acl_user_var, sizeof(acl_user_var), "vpns_user_x%d", i);
            snprintf(acl_public_var, sizeof(acl_public_var), "vpns_public_x%d", i);

            char *acl_user = nvram_safe_get(acl_user_var);
            char *acl_public = nvram_safe_get(acl_public_var);

            if (!acl_user || !*acl_user || !acl_public || !*acl_public || strncmp(result, acl_public, strlen(acl_public)) || result[strlen(acl_public)] != '\t') {
                continue;
            }

            char *tokens[8], *saveptr;
            int token_count = 0;
            char *token = strtok_r(result, "\t", &saveptr);

            // <public-key> <preshared-key> <endpoint> <allowed-ips> <latest-handshake> <transfer-rx> <transfer-tx> <persistent-keepalive>
            while (token && token_count < 8) {
                tokens[token_count++] = token;
                token = strtok_r(NULL, "\t", &saveptr);
            }

            // Если <latest-handshake> равен 0 - пропускаем
            if (token_count < 7 || !strtoul(tokens[4], NULL, 10)) {
                continue;
            }

            if (token_count >= 7) {
                fprintf(fp_leases, "%s %s %s %s %s %s\n",
                    tokens[4], tokens[3], tokens[2], acl_user, tokens[5], tokens[6]);
                break;
            }
        }
    }

    fclose(fp_leases);
    pclose(fp);
}
#endif
