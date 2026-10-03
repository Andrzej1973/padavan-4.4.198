#if defined(APP_DOH)
static int ej_doh_value(int eid, webs_t wp, int argc, char **argv)
{
    const char *names[] = {"doh_enable", "doh_server0", "doh_server1", "doh_server2", "doh_server3",
        "doh_quic", "doh_bootstrap_dns", "doh_listen_port", "doh_listen_mode", "doh_mode"};
    const unsigned char *value;
    char *name;
    unsigned int i;
    int result = 0, allowed = 0;
    if (!get_login_safe() || ejArgs(argc, argv, "%s", &name) != 1)
        return 0;
    for (i = 0; i < sizeof(names) / sizeof(names[0]); i++)
        if (!strcmp(name, names[i])) allowed = 1;
    if (!allowed) return 0;
    value = (const unsigned char *)nvram_safe_get(name);
    for (; *value; value++) {
        if (*value == '&') result += websWrite(wp, "%s", "&amp;");
        else if (*value == '<') result += websWrite(wp, "%s", "&lt;");
        else if (*value == '>') result += websWrite(wp, "%s", "&gt;");
        else if (*value == '"') result += websWrite(wp, "%s", "&quot;");
        else if (*value == 39) result += websWrite(wp, "%s", "&#39;");
        else result += websWrite(wp, "%c", *value);
    }
    return result;
}
#endif
