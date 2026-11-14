#!/usr/bin/env python3
"""Reuse the actual reaper composition fixture with physical lifetime active."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'check-initial-idle-join.py').read_text()
anchor="_,body=idle['retirement'](work,body)"
assert source.count(anchor)==1
source=source.replace(anchor,"work,body=idle['retirement'](work,body)\nphysical=runpy.run_path(str(here/'physical-stop-executor.py'))\nwork,body=physical['compose_retirement'](work,body)")
source=source.replace('#include "mbss-reaper-gate.h"','#include "mbss-reaper-gate.h"\n#include "physical-stop-lifetime.h"')
source=source.replace(' struct {int active;} wr_iot_idle_probe;', ' struct {int active;} wr_iot_idle_probe;\n struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;\n struct {int active;} wr_iot_physical_rebind_probe;')
source=source.replace('if(fault==5)ad.wr_iot_idle_probe.active=1;', 'if(fault==5)ad.wr_iot_physical_lifetime.active=1;')
source=source.replace('assert(ad.wr_iot_idle_probe.active);','assert(ad.wr_iot_physical_lifetime.active);')
source=source.replace('PASS actual reaper with idle-probe fence:', 'PASS actual reaper with physical lifetime fence:')
source=source.replace("'-fsanitize=address,undefined',", "'-fsanitize=address,undefined','-fno-pie','-no-pie',")
# Test the installed reaper body and existing reference-return implementation;
# only the extra physical lifetime storage/kernel context is injected.
exec(compile(source,str(here/'check-initial-idle-join.py'),'exec'),{'__file__':str(here/'check-initial-idle-join.py'),'__name__':'__main__'})
