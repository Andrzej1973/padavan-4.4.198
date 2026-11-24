#!/usr/bin/env python3
"""Prepare the requested/observed Zapret2 service control in Padavan."""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"Zapret2 WebUI anchor changed: {label}")
    return text.replace(old, new, 1)


def prepare_webui(tree: Path) -> None:
    user = tree / "trunk/user"
    cflags_path = user / "shared/cflags.mk"
    variables_path = user / "httpd/variables.c"
    defaults_path = user / "shared/defaults.c"
    services_path = user / "rc/services.c"
    rc_path = user / "rc/rc.c"
    rc_header_path = user / "rc/rc.h"
    web_path = user / "httpd/web_ex.c"
    page_path = user / "www/n56u_ribbon_fixed/Advanced_Services_Zapret2.asp"

    cflags = cflags_path.read_text(encoding="utf-8")
    anchor = (
        "ifeq ($(CONFIG_FIRMWARE_INCLUDE_IPERF3),y)\n"
        "CFLAGS += -DAPP_IPERF3\n"
        "endif\n"
    )
    addition = (
        "\nifeq ($(CONFIG_FIRMWARE_INCLUDE_ZAPRET2),y)\n"
        "CFLAGS += -DAPP_ZAPRET2\n"
        "endif\n"
    )
    cflags = replace_once(cflags, anchor, anchor + addition, "cflags selector")
    cflags_path.write_text(cflags, encoding="utf-8", newline="\n")

    variables = variables_path.read_text(encoding="utf-8")
    iperf_vars = (
        "#if defined (APP_IPERF3)\n"
        '\t\t\t{"iperf3_enable", "", NULL, EVM_RESTART_IPERF3},\n'
        "#endif\n"
    )
    strategy_slots = range(1, 11)
    strategy_files = "".join(
        f'\t\t\t{{"scripts.zapret2.args.{slot}", "File", NULL, EVM_RESTART_FIREWALL}},\n'
        for slot in strategy_slots
    )
    zapret_vars = (
        "#if defined(APP_ZAPRET2)\n"
        '\t\t\t{"zapret2_enable", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"zapret2_log", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"zapret2_host_auto", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"zapret2_post_enable", "", NULL, EVM_RESTART_FIREWALL|EVM_BLOCK_UNSAFE},\n'
        '\t\t\t{"zapret2_iface", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"zapret2_clients_mode", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"zapret2_profile", "", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.args", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.clients-exclude", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.destinations", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.destinations-exclude", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.hosts", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.hosts-exclude", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.hosts-auto", "File", NULL, EVM_RESTART_FIREWALL},\n'
        '\t\t\t{"scripts.zapret2.post-start.sh", "File", NULL, EVM_RESTART_FIREWALL|EVM_BLOCK_UNSAFE},\n'
        + strategy_files + "#endif\n"
    )
    variables = replace_once(
        variables, iperf_vars, iperf_vars + zapret_vars, "NVRAM variables"
    )
    variables_path.write_text(variables, encoding="utf-8", newline="\n")

    defaults = defaults_path.read_text(encoding="utf-8")
    iperf_default = (
        "#if defined (APP_IPERF3)\n"
        "\t/* iperf3 */\n"
        '\t{ "iperf3_enable", "0" },\n'
        "#endif\n"
    )
    zapret_default = (
        "\n#if defined (APP_ZAPRET2)\n"
        "\t/* Zapret2 is factory-off until the user supplies a strategy. */\n"
        '\t{ "zapret2_enable", "0" },\n'
        '\t{ "zapret2_profile", "0" },\n'
        '\t{ "zapret2_log", "0" },\n'
        '\t{ "zapret2_host_auto", "0" },\n'
        '\t{ "zapret2_post_enable", "0" },\n'
        '\t{ "zapret2_iface", "" },\n'
        '\t{ "zapret2_clients_mode", "exclude" },\n'
        "#endif\n"
    )
    defaults = replace_once(
        defaults, iperf_default, iperf_default + zapret_default, "factory default"
    )
    defaults_path.write_text(defaults, encoding="utf-8", newline="\n")

    services = services_path.read_text(encoding="utf-8")
    iperf_service = (
        "#if defined(APP_IPERF3)\n"
        "int is_iperf3_run(void){\n"
        '\tif (check_if_file_exist("/usr/bin/iperf3"))\n'
        "\t{\n"
        '\t\tif (pids("iperf3"))\n'
        "\t\t\treturn 1;\n"
        "\t}\n"
        "\treturn 0;\n"
        "}\n\n"
        "void stop_iperf3(void){\n"
        '\teval("/usr/bin/iperf3.sh","stop");\n'
        "}\n\n"
        "void start_iperf3(void){\n"
        '\tint iperf3_mode = nvram_get_int("iperf3_enable");\n'
        "\tif ( iperf3_mode == 1)\n"
        '\t\teval("/usr/bin/iperf3.sh","start");\n'
        "}\n\n"
        "void restart_iperf3(void){\n"
        "\tstop_iperf3();\n"
        "\tstart_iperf3();\n"
        "}\n"
        "#endif\n"
    )
    zapret_service = """\
#if defined(APP_ZAPRET2)
int is_zapret2_run(void){
\tif (check_if_file_exist("/usr/sbin/nfqws2"))
\t{
\t\tif (pids("nfqws2"))
\t\t\treturn 1;
\t}
\treturn 0;
}

void stop_zapret2(void){
\teval("/usr/sbin/zapret2","stop");
}

void start_zapret2(void){
\tint zapret2_mode = nvram_get_int("zapret2_enable");
\tif (zapret2_mode == 1)
\t\teval("/usr/sbin/zapret2","start");
}

void restart_zapret2(void){
\tstop_zapret2();
\tstart_zapret2();
}
#endif
"""
    services = replace_once(
        services, iperf_service, iperf_service + zapret_service, "service lifecycle"
    )
    services = replace_once(
        services,
        "#if defined(APP_IPERF3)\n\tstart_iperf3();\n#endif\n",
        "#if defined(APP_IPERF3)\n\tstart_iperf3();\n#endif\n"
        "#if defined(APP_ZAPRET2)\n\tstart_zapret2();\n#endif\n",
        "boot start",
    )
    services = replace_once(
        services,
        "#if defined(APP_IPERF3)\n\tstop_iperf3();\n#endif\n",
        "#if defined(APP_IPERF3)\n\tstop_iperf3();\n#endif\n"
        "#if defined(APP_ZAPRET2)\n\tstop_zapret2();\n#endif\n",
        "shutdown stop",
    )
    services_path.write_text(services, encoding="utf-8", newline="\n")

    rc_header = rc_header_path.read_text(encoding="utf-8")
    rc_header = replace_once(
        rc_header,
        "void start_iperf3(void);\nvoid restart_iperf3(void);\n",
        "void start_iperf3(void);\nvoid restart_iperf3(void);\n"
        "int is_zapret2_run(void);\n"
        "void stop_zapret2(void);\n"
        "void start_zapret2(void);\n"
        "void restart_zapret2(void);\n",
        "service prototypes",
    )
    rc_header_path.write_text(rc_header, encoding="utf-8", newline="\n")

    rc = rc_path.read_text(encoding="utf-8")
    rc_iperf = (
        "#if defined(APP_IPERF3)\n"
        "\t\telse if (strcmp(entry->d_name, RCN_RESTART_IPERF3) == 0)\n"
        "\t\t{\n"
        "\t\t\trestart_iperf3();\n"
        "\t\t}\n"
        "#endif\n"
    )
    firewall_dispatch = """\
\t\telse if (strcmp(entry->d_name, RCN_RESTART_NETFILTER) == 0)
\t\t{
\t\t\tupdate_router_mode();
\t\t\treload_nat_modules();
\t\t\trestart_firewall();
\t\t\tflush_conntrack_table(NULL);
\t\t}
\t\telse if (strcmp(entry->d_name, RCN_RESTART_FIREWALL) == 0)
\t\t{
\t\t\treload_nat_modules();
\t\t\trestart_firewall();
\t\t}
\t\telse if (strcmp(entry->d_name, "restart_firewall_wan") == 0)
\t\t{
\t\t\trestart_firewall();
\t\t}
"""
    firewall_reapply = """\
#if defined(APP_ZAPRET2)
#define WR_ZAPRET2_REAPPLY() restart_zapret2()
#else
#define WR_ZAPRET2_REAPPLY() do { } while (0)
#endif
\t\telse if (strcmp(entry->d_name, RCN_RESTART_NETFILTER) == 0)
\t\t{
\t\t\tupdate_router_mode();
\t\t\treload_nat_modules();
\t\t\trestart_firewall();
\t\t\tWR_ZAPRET2_REAPPLY();
\t\t\tflush_conntrack_table(NULL);
\t\t}
\t\telse if (strcmp(entry->d_name, RCN_RESTART_FIREWALL) == 0)
\t\t{
\t\t\treload_nat_modules();
\t\t\trestart_firewall();
\t\t\tWR_ZAPRET2_REAPPLY();
\t\t}
\t\telse if (strcmp(entry->d_name, "restart_firewall_wan") == 0)
\t\t{
\t\t\trestart_firewall();
\t\t\tWR_ZAPRET2_REAPPLY();
\t\t}
"""
    rc = replace_once(
        rc, firewall_dispatch, firewall_reapply, "firewall reapply"
    )
    rc_path.write_text(rc, encoding="utf-8", newline="\n")

    web = web_path.read_text(encoding="utf-8")
    web = replace_once(
        web,
        "#if defined(APP_IPERF3)\n\tint found_app_iperf3 = 1;\n#else\n"
        "\tint found_app_iperf3 = 0;\n#endif\n",
        "#if defined(APP_IPERF3)\n\tint found_app_iperf3 = 1;\n#else\n"
        "\tint found_app_iperf3 = 0;\n#endif\n"
        "#if defined(APP_ZAPRET2)\n\tint found_app_zapret2 = 1;\n#else\n"
        "\tint found_app_zapret2 = 0;\n#endif\n",
        "found-app variable",
    )
    web = replace_once(
        web,
        '\t\t"function found_app_iperf3() { return %d;}\\n"\n',
        '\t\t"function found_app_iperf3() { return %d;}\\n"\n'
        '\t\t"function found_app_zapret2() { return %d;}\\n"\n',
        "JavaScript feature query",
    )
    web = replace_once(
        web,
        "\t\tfound_app_iperf3,\n",
        "\t\tfound_app_iperf3,\n\t\tfound_app_zapret2,\n",
        "feature-query arguments",
    )
    array_anchor = "struct ej_handler ej_handlers[] =\n"
    system_entry = '\t{ "json_system_status", ej_system_status_hook},\n'
    handler = r'''
static int wr_process_present(const char *name);
static int wr_zapret2_command_state(const char *command)
{
 int result = system(command);
 if (result == -1 || !WIFEXITED(result)) return 2;
 result = WEXITSTATUS(result);
 return result == 0 ? 1 : (result == 1 ? 0 : 2);
}
static int wr_zapret2_rules_state(void)
{
 const char *wan, *mode;
 char command[256];
 int state;
#if defined(APP_ZAPRET2)
 wan = nvram_get("zapret2_iface");
 if (!wan || !wan[0]) wan = nvram_get("wan_ifname");
 if (!wan || !wan[0]) wan = nvram_get("wan0_ifname");
 if (!wan || !wan[0] || strlen(wan) > 15) return 2;
 for (state = 0; wan[state]; state++)
  if (!isalnum((unsigned char)wan[state]) &&
      wan[state] != '_' && wan[state] != '.' &&
      wan[state] != ':' && wan[state] != '-')
   return 2;
 snprintf(command, sizeof(command),
  "/usr/sbin/iptables -t mangle -C POSTROUTING -o '%s' -j ZAPRET2 >/dev/null 2>&1", wan);
 state = wr_zapret2_command_state(command);
 if (state != 1) return state;
 state = wr_zapret2_command_state(
  "/usr/sbin/iptables -t mangle -C ZAPRET2 -p tcp -j NFQUEUE --queue-num 200 --queue-bypass >/dev/null 2>&1");
 if (state != 1) return state;
 mode = nvram_get("zapret2_clients_mode");
 if (mode && !strcmp(mode, "include")) {
  state = wr_zapret2_command_state(
   "/usr/sbin/iptables -t mangle -C ZAPRET2 -m set ! --match-set wr_classic_zapret2_clients src -j RETURN >/dev/null 2>&1");
  if (state != 1) return state;
 }
 return wr_zapret2_command_state(
  "/usr/sbin/iptables -t mangle -C ZAPRET2 -p udp -j NFQUEUE --queue-num 200 --queue-bypass >/dev/null 2>&1");
#else
 (void)wan; (void)mode; (void)command; (void)state;
 return 2;
#endif
}
static int wr_zapret2_strategy_state(void)
{
 struct stat info;
 char path[48] = "/etc/storage/zapret2.args";
 const char *profile = nvram_get("zapret2_profile");
 if (!profile) profile = "";
 if (!strncmp(profile, "preset", 6) && profile[6] >= '5' &&
     profile[6] <= '9' && !profile[7]) {
  if (stat("/etc/storage/zapret2.hosts", &info) != 0 ||
      !S_ISREG(info.st_mode) || info.st_size <= 0 || info.st_size > 8192) return 0;
  snprintf(path, sizeof(path), "/usr/share/zapret2/presets/strategy%c", profile[6]);
 } else if (profile[0] && strcmp(profile, "0")) {
  if (!((profile[0] >= '1' && profile[0] <= '9' && !profile[1]) ||
        !strcmp(profile, "10"))) return 2;
  snprintf(path, sizeof(path), "/etc/storage/zapret2.args.%s", profile);
 }
 if (stat(path, &info) == 0)
  return S_ISREG(info.st_mode) && info.st_size > 0 && info.st_size <= 8192 ? 1 : 0;
 return errno == ENOENT ? 0 : 2;
}
/* Separate saved, process, rules and strategy states; bypass effect is unverified. */
static int ej_wr_zapret2_status(int eid, webs_t wp, int argc, char **argv)
{
 int requested = 0, process = 2, rules = 2, strategy = 2, found = -1;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "{\"requested\":0,\"process\":2,\"rules\":2,\"strategy\":2}");
#if defined(APP_ZAPRET2)
 requested = nvram_get_int("zapret2_enable") > 0;
 if (!access("/proc/self/stat", R_OK)) {
  found = wr_process_present("nfqws2");
  process = found < 0 ? 2 : (found > 0);
 }
 strategy = wr_zapret2_strategy_state();
 rules = wr_zapret2_rules_state();
#endif
 return websWrite(wp,
  "{\"requested\":%d,\"process\":%d,\"rules\":%d,\"strategy\":%d}",
  requested, process, rules, strategy);
}
'''
    web = replace_once(web, array_anchor, handler + "\n" + array_anchor, "HTTP handler")
    web = replace_once(
        web,
        system_entry,
        system_entry
        + '\t{ "wr_zapret2_status", ej_wr_zapret2_status},\n',
        "HTTP route",
    )
    web_path.write_text(web, encoding="utf-8", newline="\n")

    page = Path(__file__).with_name(page_path.name).read_text(encoding="utf-8")
    if page_path.exists():
        raise SystemExit("Zapret2 page already exists")
    zapret_rows = r'''<tr id="row_zapret2">
                                            <th width="50%"><#WRZapret2Title#></th>
                                            <td>
                                                <div class="main_itoggle">
                                                    <div id="zapret2_enable_on_of">
                                                        <input type="checkbox" id="zapret2_enable_fake" <% nvram_match_x("", "zapret2_enable", "1", "value=1 checked"); %><% nvram_match_x("", "zapret2_enable", "0", "value=0"); %>>
                                                    </div>
                                                </div>
                                                <div style="position: absolute; margin-left: -10000px;">
                                                    <input type="radio" name="zapret2_enable" id="zapret2_enable_1" class="input" value="1" <% nvram_match_x("", "zapret2_enable", "1", "checked"); %>/><#checkbox_Yes#>
                                                    <input type="radio" name="zapret2_enable" id="zapret2_enable_0" class="input" value="0" <% nvram_match_x("", "zapret2_enable", "0", "checked"); %>/><#checkbox_No#>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr id="wr_zapret2_status_row">
                                            <th><#WRZapret2ObservedTitle#></th>
                                            <td><strong id="wr_zapret2_status" role="status"><#WRZapret2Unknown#></strong>
                                                <button type="button" class="btn" onclick="wrZapret2Refresh()"><#WRZapret2Refresh#></button>
                                                <small id="wr_zapret2_observed_at"><#WRZapret2NoObservation#></small>
                                                <p class="help-block"><#WRZapret2ObservedNote#></p>
                                                <p><#WRZapret2ProcessLabel#>: <span id="wr_zapret2_process_detail">—</span>;
                                                <#WRZapret2RulesLabel#>: <span id="wr_zapret2_rules_detail">—</span>;
                                                <#WRZapret2StrategyLabel#>: <span id="wr_zapret2_strategy_detail">—</span></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_iface"><#WRZapret2Interface#></label></th>
                                            <td><input id="zapret2_iface" name="zapret2_iface" type="text" maxlength="15" pattern="[A-Za-z0-9_.:\-]{1,15}">
                                                <p class="help-block"><#WRZapret2InterfaceHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_log"><#WRZapret2Logging#></label></th>
                                            <td><select id="zapret2_log" name="zapret2_log">
                                                <option value="0" <% nvram_match_x("", "zapret2_log", "0", "selected"); %>><#checkbox_No#></option>
                                                <option value="1" <% nvram_match_x("", "zapret2_log", "1", "selected"); %>><#checkbox_Yes#></option>
                                            </select></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_host_auto"><#WRZapret2AutoLearn#></label></th>
                                            <td><select id="zapret2_host_auto" name="zapret2_host_auto">
                                                <option value="0" <% nvram_match_x("", "zapret2_host_auto", "0", "selected"); %>><#checkbox_No#></option>
                                                <option value="1" <% nvram_match_x("", "zapret2_host_auto", "1", "selected"); %>><#checkbox_Yes#></option>
                                            </select></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_post_enable"><#WRZapret2PostEnable#></label></th>
                                            <td><select id="zapret2_post_enable" name="zapret2_post_enable">
                                                <option value="0" <% nvram_match_x("", "zapret2_post_enable", "0", "selected"); %>><#checkbox_No#></option>
                                                <option value="1" <% nvram_match_x("", "zapret2_post_enable", "1", "selected"); %>><#checkbox_Yes#></option>
                                            </select></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_clients_mode"><#WRZapret2ClientMode#></label></th>
                                            <td><select id="zapret2_clients_mode" name="zapret2_clients_mode">
                                                <option value="exclude" <% nvram_match_x("", "zapret2_clients_mode", "exclude", "selected"); %>><#WRZapret2ExcludeMode#></option>
                                                <option value="include" <% nvram_match_x("", "zapret2_clients_mode", "include", "selected"); %>><#WRZapret2IncludeMode#></option>
                                            </select></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_clients_exclude"><#WRZapret2ExcludedClients#></label></th>
                                            <td><textarea id="zapret2_clients_exclude" name="scripts.zapret2.clients-exclude" data-zapret2-file rows="4" maxlength="4096" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.clients-exclude",""); %></textarea>
                                                <p class="help-block"><#WRZapret2ExcludedClientsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_destinations"><#WRZapret2IncludedDestinations#></label></th>
                                            <td><textarea id="zapret2_destinations" name="scripts.zapret2.destinations" data-zapret2-file rows="4" maxlength="4096" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.destinations",""); %></textarea>
                                                <p class="help-block"><#WRZapret2ExcludedClientsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_destinations_exclude"><#WRZapret2ExcludedDestinations#></label></th>
                                            <td><textarea id="zapret2_destinations_exclude" name="scripts.zapret2.destinations-exclude" data-zapret2-file rows="4" maxlength="4096" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.destinations-exclude",""); %></textarea>
                                                <p class="help-block"><#WRZapret2ExcludedClientsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_hosts"><#WRZapret2Domains#></label></th>
                                            <td><textarea id="zapret2_hosts" name="scripts.zapret2.hosts" data-zapret2-file rows="4" maxlength="8192" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.hosts",""); %></textarea>
                                                <p class="help-block"><#WRZapret2DomainsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_hosts-exclude"><#WRZapret2DomainsExclude#></label></th>
                                            <td><textarea id="zapret2_hosts-exclude" name="scripts.zapret2.hosts-exclude" data-zapret2-file rows="4" maxlength="8192" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.hosts-exclude",""); %></textarea>
                                                <p class="help-block"><#WRZapret2DomainsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_hosts-auto"><#WRZapret2AutoDomains#></label></th>
                                            <td><textarea id="zapret2_hosts-auto" name="scripts.zapret2.hosts-auto" data-zapret2-file rows="4" maxlength="8192" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.hosts-auto",""); %></textarea>
                                                <p class="help-block"><#WRZapret2DomainsHelp#></p></td>
                                        </tr>
                                        <tr>
                                            <th><label for="zapret2_post-start.sh"><#WRZapret2PostScript#></label></th>
                                            <td><textarea id="zapret2_post-start.sh" name="scripts.zapret2.post-start.sh" data-zapret2-file rows="4" maxlength="8192" class="span12" spellcheck="false"><% nvram_dump("scripts.zapret2.post-start.sh",""); %></textarea>
                                                <p class="help-block"><#WRZapret2DomainsHelp#></p></td>
                                        </tr>
                                        <tr id="row_zapret2_strategy">
                                            <th><label for="zapret2_strategy"><#WRZapret2StrategyTitle#></label></th>
                                            <td><textarea id="zapret2_strategy" rows="12" wrap="off" spellcheck="false" maxlength="8192" class="span12" name="scripts.zapret2.args" style="font-family:'Courier New'; font-size:12px;"><% nvram_dump("scripts.zapret2.args",""); %></textarea>
                                                <p class="help-block"><#WRZapret2StrategyHelp#></p></td>
                                        </tr>'''
    profile_options = "".join(
        f'<option value="{slot}" <% nvram_match_x("", "zapret2_profile", "{slot}", "selected"); %>>{slot}</option>'
        for slot in range(11)
    )
    profile_options += "".join(
        f'<option value="preset{slot}" <% nvram_match_x("", "zapret2_profile", "preset{slot}", "selected"); %>><#WRZapret2Preset#> {slot}</option>'
        for slot in range(5, 10)
    )
    profile_selector = (
        '<tr><th><label for="zapret2_profile"><#WRZapret2Profile#></label></th>'
        f'<td><select name="zapret2_profile" id="zapret2_profile">{profile_options}</select></td></tr>'
    )
    strategy_rows = "".join(
        f'<tr data-zapret2-profile="{slot}" hidden><th><#WRZapret2Profile#> {slot}</th><td>'
        f'<textarea aria-label="<#WRZapret2Profile#> {slot}" rows="12" wrap="off" spellcheck="false" '
        f'maxlength="8192" class="span12" name="scripts.zapret2.args.{slot}">'
        f'<% nvram_dump("scripts.zapret2.args.{slot}",""); %></textarea></td></tr>'
        for slot in strategy_slots
    )
    zapret_rows = zapret_rows.replace(
        '<tr id="row_zapret2_strategy">',
        profile_selector + '<tr id="row_zapret2_strategy" data-zapret2-profile="0">',
        1,
    ) + strategy_rows
    script = r'''
var wrZapret2StatusBusy = false;
var wrZapret2Generation = 0, wrZapret2SampledAt = 0;
$j(function () {
    var profile = document.getElementById('zapret2_profile');
    if (!profile) return;
    function showProfile() {
        $j('[data-zapret2-profile]').each(function () {
            this.hidden = this.getAttribute('data-zapret2-profile') !== profile.value;
        });
    }
    $j(profile).on('change', showProfile);
    showProfile();
    document.getElementById('zapret2_iface').value = decodeURIComponent('<% nvram_char_to_ascii("", "zapret2_iface"); %>');
});
function validZapret2() {
    var iface = document.getElementById('zapret2_iface');
    if (!iface.checkValidity()) {
        iface.reportValidity();
        return false;
    }
    if (!found_app_zapret2() || !document.form.zapret2_enable[0].checked) return true;
    var profile = document.getElementById('zapret2_profile').value;
    if (/^preset[5-9]$/.test(profile)) {
        var domains = document.getElementById('zapret2_hosts');
        if (domains.value.trim()) return true;
        alert('<#WRZapret2PresetDomains#>');
        domains.focus();
        return false;
    }
    var name = 'scripts.zapret2.args' + (profile === '0' ? '' : '.' + profile);
    var strategy = document.form.elements.namedItem(name);
    if (!strategy || !strategy.value.trim()) {
        alert('<#WRZapret2StrategyRequired#>');
        return false;
    }
    return true;
}
function wrZapret2Detail(labels, value) {
    return labels[(value === 0 || value === 1 || value === 2) ? value : 2];
}
function wrZapret2Render(data) {
    var generation = ++wrZapret2Generation;
    wrZapret2SampledAt = 0;
    var element = document.getElementById('wr_zapret2_status');
    if (!element) return;
    var valid = data && [data.requested, data.process, data.rules, data.strategy].every(function(v) {
        return v === 0 || v === 1 || v === 2;
    });
    var label, css = 'text-warning';
    if (!valid) {
        label = '<#WRZapret2Unknown#>';
    } else if (data.process === 2 || data.rules === 2) {
        label = '<#WRZapret2Unknown#>';
    } else if (data.strategy === 2) {
        label = '<#WRZapret2Unknown#>';
    } else if (!data.requested && !data.process && !data.rules) {
        label = '<#WRZapret2Off#>'; css = 'text-muted';
    } else if (data.requested && !data.strategy) {
        label = '<#WRZapret2StrategyMissing#>'; css = 'text-error';
    } else if (data.requested && data.process && data.rules) {
        label = '<#WRZapret2Running#>'; css = 'text-info';
    } else if (data.requested && !data.process && !data.rules) {
        label = '<#WRZapret2Missing#>'; css = 'text-error';
    } else if (!data.requested && (data.process || data.rules)) {
        label = '<#WRZapret2StillRunning#>';
    } else {
        label = '<#WRZapret2Inconsistent#>';
    }
    element.textContent = label;
    element.className = css;
    var stateLabels = ['<#WRZapret2Absent#>', '<#WRZapret2Present#>', '<#WRZapret2UnknownShort#>'];
    document.getElementById('wr_zapret2_process_detail').textContent =
        valid ? wrZapret2Detail(stateLabels, data.process) : stateLabels[2];
    document.getElementById('wr_zapret2_rules_detail').textContent =
        valid ? wrZapret2Detail(stateLabels, data.rules) : stateLabels[2];
    document.getElementById('wr_zapret2_strategy_detail').textContent =
        valid ? wrZapret2Detail(stateLabels, data.strategy) : stateLabels[2];
    if (valid) {
        wrZapret2SampledAt = Date.now();
        window.setTimeout(function() {
            if (generation === wrZapret2Generation) wrZapret2Render(null);
        }, 45000);
        var observedAt = document.getElementById('wr_zapret2_observed_at');
        if (observedAt) observedAt.textContent = '<#WRZapret2LastObservation#> ' + new Date().toLocaleTimeString();
    }
}
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && wrZapret2SampledAt && Date.now() - wrZapret2SampledAt >= 45000) wrZapret2Render(null);
});
function wrZapret2Refresh() {
    if (wrZapret2StatusBusy || document.hidden || !found_app_zapret2()) return;
    wrZapret2StatusBusy = true;
    $j.ajax({url:'/update.cgi', data:{output:'wr_zapret2_status'}, dataType:'json', cache:false, timeout:5000})
        .done(function(data) { wrZapret2Render(data); })
        .fail(function() { wrZapret2Render(null); })
        .always(function() { wrZapret2StatusBusy = false; });
}
'''
    page = replace_once(page, "<!-- ZAPRET2_ROWS -->", zapret_rows, "service rows")
    page = replace_once(page, "// ZAPRET2_STATUS_SCRIPT", script, "status script")
    page_path.write_text(page, encoding="utf-8", newline="\n")

    translations = {
        "EN.footer": {
            "WRZapret2Title": "Zapret2 packet processing",
            "WRZapret2Interface": "Interface",
            "WRZapret2ExcludedClients": "Client IPv4 list",
            "WRZapret2ClientMode": "Client mode",
            "WRZapret2ExcludeMode": "Exclude listed clients",
            "WRZapret2IncludeMode": "Only listed clients (requires IPSet)",
            "WRZapret2IncludedDestinations": "Destination IPv4 inclusion list",
            "WRZapret2ExcludedDestinations": "Excluded destinations",
            "WRZapret2Domains": "Domains to process",
            "WRZapret2AutoLearn": "Learn domains automatically",
            "WRZapret2PostEnable": "Run an administrator script after start",
            "WRZapret2PostScript": "Post-start shell script (runs as root)",
            "WRZapret2PostEnable": "Виконувати скрипт адміністратора після запуску",
            "WRZapret2PostScript": "Скрипт після запуску (виконується від root)",
            "WRZapret2PostEnable": "Выполнять скрипт администратора после запуска",
            "WRZapret2PostScript": "Скрипт после запуска (выполняется от root)",
            "WRZapret2AutoDomains": "Automatically learned domains",
            "WRZapret2DomainsExclude": "Excluded domains",
            "WRZapret2DomainsHelp": "Enter one domain per line. Applies to each rule profile.",
            "WRZapret2ExcludedClientsHelp": "Enter one IPv4 address or CIDR per line, up to 64 entries.",
            "WRZapret2Profile": "Strategy profile",
            "WRZapret2Preset": "Built-in strategy",
            "WRZapret2PresetDomains": "Specify domains before enabling a built-in strategy.",
            "WRZapret2RequestTooLarge": "Too many changes for one request. Apply fewer strategy edits at a time.",
            "WRZapret2InterfaceHelp": "Leave empty for automatic WAN selection.",
            "WRZapret2Logging": "Detailed system logging",
            "WRZapret2ObservedTitle": "Observed Zapret2 state",
            "WRZapret2Refresh": "Refresh status",
            "WRZapret2Unknown": "Process or rule state unknown",
            "WRZapret2Off": "Disabled; process and rules absent",
            "WRZapret2Running": "Enabled; process, strategy and rules present (traffic effect not verified)",
            "WRZapret2Missing": "Enabled; service did not start",
            "WRZapret2StillRunning": "Disabled; process or rules still present",
            "WRZapret2Inconsistent": "Inconsistent process and rule state",
            "WRZapret2StrategyMissing": "Strategy file is missing or empty",
            "WRZapret2ProcessLabel": "Process",
            "WRZapret2RulesLabel": "Rules",
            "WRZapret2StrategyLabel": "Strategy",
            "WRZapret2Present": "present",
            "WRZapret2Absent": "absent",
            "WRZapret2UnknownShort": "unknown",
            "WRZapret2LastObservation": "Last observation:",
            "WRZapret2NoObservation": "No confirmed observation yet",
            "WRZapret2ObservedNote": "This reads the saved switch, nfqws2 process, NFQUEUE hook and strategy file separately. It does not prove that bypassing works or that routed traffic is healthy. Traffic remains fail-open if the queue listener is absent.",
            "WRZapret2StrategyTitle": "nfqws2 strategy arguments",
            "WRZapret2StrategyHelp": "One or more root-managed nfqws2 arguments, for example --filter-tcp=443 --filter-l7=tls. The service supplies --qnum and pinned Lua init files automatically. Do not put shell commands here. Rules are built-in.",
            "WRZapret2StrategyRequired": "Enter a non-empty nfqws2 strategy before enabling Zapret2.",
        },
        "UK.dict": {
            "WRZapret2Title": "Обробка пакетів Zapret2",
            "WRZapret2Interface": "Інтерфейс",
            "WRZapret2ExcludedClients": "IPv4-список клієнтів",
            "WRZapret2ClientMode": "Режим для клієнтів",
            "WRZapret2ExcludeMode": "Виключити клієнтів зі списку",
            "WRZapret2IncludeMode": "Лише клієнти зі списку (потрібен IPSet)",
            "WRZapret2IncludedDestinations": "IPv4-список адрес призначення",
            "WRZapret2ExcludedDestinations": "Винятки для адрес призначення",
            "WRZapret2Domains": "Домени для обробки",
            "WRZapret2AutoLearn": "Автоматично поповнювати список доменів",
            "WRZapret2AutoDomains": "Автоматично додані домени",
            "WRZapret2DomainsExclude": "Винятки для доменів",
            "WRZapret2DomainsHelp": "Введіть по одному домену на рядок. Список діє для кожного профілю правил.",
            "WRZapret2ExcludedClientsHelp": "Введіть до 64 IPv4-адрес або підмереж CIDR, по одній на рядок.",
            "WRZapret2Profile": "Профіль стратегії",
            "WRZapret2Preset": "Готова стратегія",
            "WRZapret2PresetDomains": "Вкажіть домени перед увімкненням готової стратегії.",
            "WRZapret2RequestTooLarge": "Забагато змін для одного запиту. Застосуйте зміни до меншої кількості стратегій за раз.",
            "WRZapret2InterfaceHelp": "Порожнє поле вибирає WAN автоматично.",
            "WRZapret2Logging": "Докладний системний журнал",
            "WRZapret2ObservedTitle": "Спостережений стан Zapret2",
            "WRZapret2Refresh": "Оновити стан",
            "WRZapret2Unknown": "Стан процесу або правил невідомий",
            "WRZapret2Off": "Вимкнено; процесу й правил немає",
            "WRZapret2Running": "Увімкнено; процес, стратегія й правила наявні (вплив на трафік не перевірено)",
            "WRZapret2Missing": "Увімкнено; служба не запустилася",
            "WRZapret2StillRunning": "Вимкнено; процес або правила досі наявні",
            "WRZapret2Inconsistent": "Неузгоджений стан процесу й правил",
            "WRZapret2StrategyMissing": "Файл стратегії відсутній або порожній",
            "WRZapret2ProcessLabel": "Процес",
            "WRZapret2RulesLabel": "Правила",
            "WRZapret2StrategyLabel": "Стратегія",
            "WRZapret2Present": "наявний",
            "WRZapret2Absent": "відсутній",
            "WRZapret2UnknownShort": "невідомо",
            "WRZapret2LastObservation": "Останнє спостереження:",
            "WRZapret2NoObservation": "Підтвердженого спостереження ще немає",
            "WRZapret2ObservedNote": "Окремо читаються збережений перемикач, процес nfqws2, хук NFQUEUE і файл стратегії. Це не доводить ефективність обходу або справність маршрутизованого трафіку. За відсутності обробника черга працює fail-open.",
            "WRZapret2StrategyTitle": "Аргументи стратегії nfqws2",
            "WRZapret2StrategyHelp": "Один або кілька root-керованих аргументів nfqws2, наприклад --filter-tcp=443 --filter-l7=tls. Сервіс сам додає --qnum і закріплені Lua-файли. Не вводьте сюди shell-команди. Правила вбудовані.",
            "WRZapret2StrategyRequired": "Введіть непорожню стратегію nfqws2 перед увімкненням Zapret2.",
        },
        "RU.dict": {
            "WRZapret2Title": "Обработка пакетов Zapret2",
            "WRZapret2Interface": "Интерфейс",
            "WRZapret2ExcludedClients": "IPv4-список клиентов",
            "WRZapret2ClientMode": "Режим для клиентов",
            "WRZapret2ExcludeMode": "Исключить клиентов из списка",
            "WRZapret2IncludeMode": "Только клиенты из списка (нужен IPSet)",
            "WRZapret2IncludedDestinations": "IPv4-список адрес назначения",
            "WRZapret2ExcludedDestinations": "Исключения для адресов назначения",
            "WRZapret2Domains": "Домены для обработки",
            "WRZapret2AutoLearn": "Автоматически пополнять список доменов",
            "WRZapret2AutoDomains": "Автоматически добавленные домены",
            "WRZapret2DomainsExclude": "Исключения для доменов",
            "WRZapret2DomainsHelp": "Введите по одному домену на строку. Список действует для каждого профиля правил.",
            "WRZapret2ExcludedClientsHelp": "Введите до 64 IPv4-адресов или подсетей CIDR, по одной на строку.",
            "WRZapret2Profile": "Профиль стратегии",
            "WRZapret2Preset": "Готовая стратегия",
            "WRZapret2PresetDomains": "Укажите домены перед включением готовой стратегии.",
            "WRZapret2RequestTooLarge": "Слишком много изменений для одного запроса. Применяйте изменения к меньшему числу стратегий за раз.",
            "WRZapret2InterfaceHelp": "Пустое поле выбирает WAN автоматически.",
            "WRZapret2Logging": "Подробный системный журнал",
            "WRZapret2ObservedTitle": "Наблюдаемое состояние Zapret2",
            "WRZapret2Refresh": "Обновить состояние",
            "WRZapret2Unknown": "Состояние процесса или правил неизвестно",
            "WRZapret2Off": "Выключено; процесса и правил нет",
            "WRZapret2Running": "Включено; процесс, стратегия и правила есть (влияние на трафик не проверено)",
            "WRZapret2Missing": "Включено; служба не запустилась",
            "WRZapret2StillRunning": "Выключено; процесс или правила всё ещё есть",
            "WRZapret2Inconsistent": "Несогласованное состояние процесса и правил",
            "WRZapret2StrategyMissing": "Файл стратегии отсутствует или пуст",
            "WRZapret2ProcessLabel": "Процесс",
            "WRZapret2RulesLabel": "Правила",
            "WRZapret2StrategyLabel": "Стратегия",
            "WRZapret2Present": "есть",
            "WRZapret2Absent": "нет",
            "WRZapret2UnknownShort": "неизвестно",
            "WRZapret2LastObservation": "Последнее наблюдение:",
            "WRZapret2NoObservation": "Подтверждённого наблюдения пока нет",
            "WRZapret2ObservedNote": "Отдельно читаются сохранённый переключатель, процесс nfqws2, хук NFQUEUE и файл стратегии. Это не доказывает эффективность обхода или исправность маршрутизируемого трафика. При отсутствии обработчика очередь работает fail-open.",
            "WRZapret2StrategyTitle": "Аргументы стратегии nfqws2",
            "WRZapret2StrategyHelp": "Один или несколько управляемых root аргументов nfqws2, например --filter-tcp=443 --filter-l7=tls. Служба сама добавляет --qnum и закреплённые Lua-файлы. Не вводите здесь shell-команды. Правила встроены.",
            "WRZapret2StrategyRequired": "Введите непустую стратегию nfqws2 перед включением Zapret2.",
        },
    }
    for filename, values in translations.items():
        path = user / "www/dict" / filename
        content = path.read_text(encoding="utf-8")
        if "WRZapret2Unknown=" in content:
            raise SystemExit(f"Zapret2 labels already exist in {filename}")
        content = (
            content.rstrip("\n")
            + "\n"
            + "\n".join(f"{key}={value}" for key, value in values.items())
            + "\n"
        )
        path.write_text(content, encoding="utf-8", newline="\n")

    verify_prepared(tree)


def verify_prepared(tree: Path) -> None:
    user = tree / "trunk/user"
    required = {
        user / "shared/cflags.mk": "-DAPP_ZAPRET2",
        user / "httpd/variables.c": "EVM_RESTART_FIREWALL",
        user / "shared/defaults.c": '{ "zapret2_enable", "0" }',
        user / "rc/services.c": "restart_zapret2",
        user / "rc/rc.h": "restart_zapret2",
        user / "rc/rc.c": "WR_ZAPRET2_REAPPLY",
        user / "httpd/web_ex.c": "ej_wr_zapret2_status",
        user / "www/n56u_ribbon_fixed/Advanced_Services_Zapret2.asp":
            'id="wr_zapret2_status"',
    }
    for path, marker in required.items():
        if marker not in path.read_text(encoding="utf-8"):
            raise SystemExit(f"Zapret2 verification marker missing in {path}: {marker}")
    for filename in ("EN.footer", "UK.dict", "RU.dict"):
        text = (user / "www/dict" / filename).read_text(encoding="utf-8")
        if "WRZapret2StrategyRequired=" not in text:
            raise SystemExit(f"Zapret2 localized label missing in {filename}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Padavan tree root")
    args = parser.parse_args()
    prepare_webui(args.tree)
    print("Prepared Zapret2 requested/observed WebUI and restart lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
