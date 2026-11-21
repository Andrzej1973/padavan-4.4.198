#!/usr/bin/env python3
"""In-memory regression checks for WR1200JS CPU watchdog exclusion."""
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prep = load("wr_watchdog_prepare", root / "prepare-wr1200js-cpu-watchdog.py")
service = prep.transform_services(prep.START + "\n\n" + prep.RESTART)
assert "module_smart_load(\"rt_timer_wdg\"" not in service
assert "module_smart_unload(\"rt_timer_wdg\"" not in service
assert "start_watchdog_cpu(void)" in service and "restart_watchdog_cpu(void)" in service

defaults = prep.transform_defaults('\t{ "watchdog_cpu", "1" },')
assert '#if defined(BOARD_WR1200JS)\n\t{ "watchdog_cpu", "0" },' in defaults
assert '#else\n\t{ "watchdog_cpu", "1" },\n#endif' in defaults

page = prep.transform_page('''\tinit_itoggle('watchdog_cpu');
<tr>
    <th width="50%"><a class="help_tooltip" href="#"><#TweaksWdg#></a></th>
    <td><div id="watchdog_cpu_on_of"><input name="watchdog_cpu"></div></td>
</tr>
<tr id="wrWatchdog_status_row"><td>observer retained</td></tr>
''')
assert "init_itoggle('watchdog_cpu')" not in page
assert "watchdog_cpu_on_of" not in page and "name=\"watchdog_cpu\"" not in page
assert "wrWatchdog_status_row" in page

nav = load("services_nav", root / "services-nav/prepare-unified-nav.py")
assert nav.service_excluded("WRServicesNavWatchdog", {"watchdog_cpu"})
assert not nav.service_excluded("WRServicesNavCron", {"watchdog_cpu"})
assert not nav.service_excluded("WRServicesNavWatchdog", set())
print("PASS WR1200JS CPU watchdog control removal, inert legacy lifecycle, factory-off default, retained status, and board-scoped navigation")
