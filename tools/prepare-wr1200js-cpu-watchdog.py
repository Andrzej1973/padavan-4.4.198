#!/usr/bin/env python3
"""Disable the unsupported optional CPU watchdog on WR1200JS only."""
import argparse
from pathlib import Path
import re


START = '''void
start_watchdog_cpu(void)
{
	if (nvram_get_int("watchdog_cpu") != 0)
		module_smart_load("rt_timer_wdg", NULL);
}'''
RESTART = '''void
restart_watchdog_cpu(void)
{
	if (nvram_get_int("watchdog_cpu") == 0)
		module_smart_unload("rt_timer_wdg", 0);
	else
		module_smart_load("rt_timer_wdg", NULL);
}'''
INERT = '''/* WR1200JS does not ship rt_timer_wdg. Ignore legacy NVRAM values. */
void
start_watchdog_cpu(void)
{
}

void
restart_watchdog_cpu(void)
{
}'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one {label} anchor")
    return text.replace(old, new, 1)


def transform_services(service_text: str) -> str:
    return replace_once(service_text, START + "\n\n" + RESTART, INERT,
                        "CPU watchdog lifecycle")


def transform_defaults(defaults_text: str) -> str:
    return replace_once(
        defaults_text,
        '\t{ "watchdog_cpu", "1" },',
        '#if defined(BOARD_WR1200JS)\n\t{ "watchdog_cpu", "0" },\n'
        '#else\n\t{ "watchdog_cpu", "1" },\n#endif',
        "CPU watchdog default",
    )

def transform_page(page_text: str) -> str:
    init = "\tinit_itoggle('watchdog_cpu');\n"
    page_text = replace_once(page_text, init, "", "CPU watchdog toggle initializer")
    control_row = re.compile(
        r"^[ \t]*<tr>\r?\n"
        r"[ \t]*<th width=\"50%\"><a class=\"help_tooltip\"[^\n]*"
        r"<#TweaksWdg#>[\s\S]*?^[ \t]*</tr>",
        re.MULTILINE,
    )
    page_text, count = control_row.subn("", page_text, count=1)
    if count != 1 or 'id="watchdog_cpu_on_of"' in page_text:
        raise SystemExit("Could not remove exactly the CPU watchdog control row")
    return page_text


def prepare(source: Path) -> None:
    user = source / "trunk/user"
    board_mk = source / "trunk/configs/boards/WR1200JS/board.mk"
    services = user / "rc/services.c"
    defaults = user / "shared/defaults.c"
    page = user / "www/n56u_ribbon_fixed/Advanced_Services_Content.asp"

    if not board_mk.is_file() or "-DBOARD_WR1200JS" not in board_mk.read_text(encoding="utf-8"):
        raise SystemExit("WR1200JS board identity is missing; refusing board-specific transform")

    service_text = transform_services(services.read_text(encoding="utf-8"))
    defaults_text = transform_defaults(defaults.read_text(encoding="utf-8"))
    page_text = transform_page(page.read_text(encoding="utf-8"))

    services.write_text(service_text, encoding="utf-8", newline="\n")
    defaults.write_text(defaults_text, encoding="utf-8", newline="\n")
    page.write_text(page_text, encoding="utf-8", newline="\n")
    print("Prepared WR1200JS: CPU watchdog control removed, legacy lifecycle inert, default off")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Pinned Padavan source tree")
    args = parser.parse_args()
    prepare(args.source)


if __name__ == "__main__":
    main()
