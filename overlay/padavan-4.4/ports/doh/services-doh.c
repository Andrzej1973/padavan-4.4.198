/* Included from services.c under APP_DOH. Existing NVRAM is preserved. */
int is_doh_run(void)
{
    return check_if_file_exist("/usr/sbin/https_dns_proxy") && pids("https_dns_proxy") != 0;
}
void stop_doh(void)
{
    if (eval("/usr/bin/doh_proxy.sh", "stop") != 0)
        logmessage("DoH", "Failed to stop service");
}
int start_doh(void)
{
    if (!get_ap_mode() && nvram_match("doh_enable", "1"))
        return eval("/usr/bin/doh_proxy.sh", "start");
    return 0;
}
void restart_doh(void)
{
    if (!get_ap_mode() && nvram_match("doh_enable", "1")) {
        if (eval("/usr/bin/doh_proxy.sh", "restart") != 0)
            logmessage("DoH", "Failed to restart service");
    } else {
        stop_doh();
    }
}
