#!/usr/bin/env python3
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPTIONS = (0, 6, 12, 24, 48, 72, 168, 336)
LABELS = {
    "EN.footer": ("Enable IPSet updates", "Update interval (hours)", "HTTPS sources", "Enter one set name and HTTPS URL per line. Interval 0 updates only after settings change or startup."),
    "UK.dict": ("Увімкнути оновлення IPSet", "Інтервал оновлення (години)", "Джерела HTTPS", "Введіть назву набору й адресу HTTPS по одному джерелу на рядок. Інтервал 0 оновлює лише після зміни налаштувань або запуску."),
    "RU.dict": ("Включить обновление IPSet", "Интервал обновления (часы)", "Источники HTTPS", "Введите имя набора и адрес HTTPS по одному источнику на строку. Интервал 0 обновляет только после изменения настроек или запуска."),
}


STATUS_HANDLER = """
static int ej_wr_classic_ipset_state(int eid, webs_t wp, int argc, char **argv)
{
    FILE *file;
    int pid = 0, running = 0;
    char path[64], command[256];
    size_t length, off;
    (void)eid;
    (void)argc;
    (void)argv;
    if (nvram_get_int("wr_classic_ipset_enable") != 1)
        return websWrite(wp, "0");
    file = fopen("/var/run/wr-classic-ipset.worker/pid", "r");
    if (file) {
        if (fscanf(file, "%d", &pid) != 1) pid = 0;
        fclose(file);
    }
    if (pid > 1) {
        snprintf(path, sizeof(path), "/proc/%d/cmdline", pid);
        file = fopen(path, "r");
        if (file) {
            length = fread(command, 1, sizeof(command) - 1, file);
            fclose(file);
            command[length] = 0;
            for (off = 0; off < length; off += strlen(command + off) + 1) {
                if (!strcmp(command + off, "/usr/sbin/wr-classic-ipset-watch")) {
                    running = 1;
                    break;
                }
            }
        }
    }
    return websWrite(wp, "%d", running ? 1 : 2);
}

static int ej_wr_classic_ipset_result(int eid, webs_t wp, int argc, char **argv)
{
    FILE *file = fopen("/var/run/wr-classic-ipset.status", "r");
    char state[16], extra;
    unsigned updated = 0, failed = 0;
    int valid = 0, result = 0;
    (void)eid;
    (void)argc;
    (void)argv;
    if (file) {
        valid = fscanf(file, "%15s %u %u %c", state, &updated, &failed, &extra) == 3;
        fclose(file);
    }
    if (valid && updated <= 16 && failed <= 16 && updated + failed <= 16) {
        if (!strcmp(state, "updated") && updated && !failed) result = 1;
        else if (!strcmp(state, "error")) result = 2;
        else if (!strcmp(state, "unconfigured") && !updated && !failed) result = 3;
    }
    if (!result) updated = failed = 0;
    return websWrite(wp, "[%d,%u,%u]", result, updated, failed);
}
"""


def patched(path, anchor, replacement):
    text = path.read_text(encoding="utf-8")
    if text.count(anchor) != 1 or replacement in text:
        raise SystemExit(f"Unexpected IPSet preparation anchor in {path}")
    return text.replace(anchor, replacement, 1)


def main():
    parser = argparse.ArgumentParser(description="Stage Classic IPSet integration")
    parser.add_argument("tree", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    if "CONFIG_FIRMWARE_INCLUDE_IPSET=y" not in args.config.read_text().splitlines():
        return

    user = args.tree / "trunk/user"
    variables = user / "httpd/variables.c"
    defaults = user / "shared/defaults.c"
    services = user / "rc/services.c"
    makefile = user / "Makefile"
    anchor = '\t\t\t{"iperf3_enable", "", NULL, EVM_RESTART_IPERF3},\n#endif\n'
    variable_rows = (
        '\t\t\t{"wr_classic_ipset_enable", "", NULL, 0},\n'
        '\t\t\t{"wr_classic_ipset_period", "", NULL, 0},\n'
        '\t\t\t{"scripts.wr-classic-ipset.feeds", "File", NULL, 0},\n'
    )
    default_anchor = '\t{ "iperf3_enable", "0" },\n#endif\n'
    default_rows = '\t{ "wr_classic_ipset_enable", "0" },\n\t{ "wr_classic_ipset_period", "24" },\n'
    startup = "start_services_once(int is_ap_mode)\n{\n"
    make_anchor = "all: $(patsubst %,%_only,$(dir_y))"
    files = {
        variables: patched(variables, anchor, anchor + variable_rows),
        defaults: patched(defaults, default_anchor, default_anchor + default_rows),
        services: patched(services, startup, startup + '\tdoSystem("/usr/sbin/wr-classic-ipset-watch </dev/null >/dev/null 2>&1 &");\n'),
        makefile: patched(makefile, make_anchor, "dir_y += wr-classic-ipset\n\n" + make_anchor),
    }
    web = user / "httpd/web_ex.c"
    web_text = web.read_text(encoding="utf-8")
    table = 'struct ej_handler ej_handlers[] =\n{'
    entry = '\t{ "nvram_dump", ej_dump},'
    if web_text.count(table) != 1 or web_text.count(entry) != 1 or "ej_wr_classic_ipset_state" in web_text:
        raise SystemExit("Unexpected IPSet status-handler anchor")
    files[web] = web_text.replace(table, STATUS_HANDLER + table, 1).replace(
        entry, entry + '\n\t{ "wr_classic_ipset_state", ej_wr_classic_ipset_state},' + '\n\t{ "wr_classic_ipset_result", ej_wr_classic_ipset_result},', 1
    )
    page = user / "www/n56u_ribbon_fixed/Advanced_Services_IPSet.asp"
    package = user / "wr-classic-ipset"
    if page.exists() or package.exists():
        raise SystemExit("Classic IPSet already staged")
    options = "\n".join(
        f'<option value="{hour}" <% nvram_match_x("", "wr_classic_ipset_period", "{hour}", "selected"); %>>{hour}</option>'
        for hour in OPTIONS
    )
    files[page] = (HERE / page.name).read_text(encoding="utf-8").replace("<!-- IPSET_PERIOD_OPTIONS -->", options)
    for name, values in LABELS.items():
        path = user / "www/dict" / name
        content = path.read_text(encoding="utf-8")
        if "WRIPSetEnable=" in content:
            raise SystemExit(f"Classic IPSet labels already exist in {path}")
        state_labels = {
            "EN.footer": ("Disabled", "Running", "Not running", "Service status"),
            "UK.dict": ("Вимкнено", "Працює", "Не працює", "Стан служби"),
            "RU.dict": ("Выключено", "Работает", "Не работает", "Состояние службы"),
        }[name]
        result_labels = {
            "EN.footer": ("Last refresh", "No result yet", "Updated", "Error", "No sources configured", "Successful sets", "Failed sets"),
            "UK.dict": ("Останнє оновлення", "Результату ще немає", "Оновлено", "Помилка", "Джерела не налаштовані", "Успішно", "З помилкою"),
            "RU.dict": ("Последнее обновление", "Результата пока нет", "Обновлено", "Ошибка", "Источники не настроены", "Успешно", "С ошибкой"),
        }[name]
        keys = (
            "WRIPSetEnable", "WRIPSetPeriod", "WRIPSetFeeds", "WRIPSetFeedsHelp",
            "WRIPSetDisabled", "WRIPSetRunning", "WRIPSetStopped", "WRIPSetStatus",
            "WRIPSetLastRefresh", "WRIPSetNoResult", "WRIPSetUpdated", "WRIPSetError",
            "WRIPSetUnconfigured", "WRIPSetSucceededCount", "WRIPSetFailedCount",
        )
        entries = zip(keys, values + state_labels + result_labels)
        files[path] = content.rstrip("\n") + "\n" + "".join(f"{key}={value}\n" for key, value in entries)
    package.mkdir()
    recipe = ["all clean:", "\t@:", "", "romfs:"]
    for source, target in (
        ("apply-managed-set.sh", "apply"),
        ("update-managed-feeds.sh", "refresh"),
        ("watch-managed-feeds.sh", "watch"),
    ):
        files[package / source] = (HERE / source).read_text(encoding="utf-8")
        recipe.append(f"\t$(ROMFSINST) -p +x {source} /usr/sbin/wr-classic-ipset-{target}")
    files[package / "Makefile"] = "\n".join(recipe) + "\n"
    for path, content in files.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    print("Prepared Classic IPSet page, configuration and scheduler")


if __name__ == "__main__":
    main()
