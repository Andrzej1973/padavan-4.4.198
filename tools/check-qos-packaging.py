#!/usr/bin/env python3
"""Evaluate the real Make conditional for QoS/SQM packaging without files."""
import importlib.util
from pathlib import Path
import shutil
import subprocess

source = Path(__file__).resolve().parents[1] / 'overlay/padavan-4.4/ports/qos/prepare-packaging.py'
spec = importlib.util.spec_from_file_location('qos_packaging', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
# Pinned vipshmily/padavan-4.4 c25283e915a2a00a763774dd255b14aff997285e.
fixture = '''SRC_NAME=iproute2-5.12.0
THISDIR = $(shell pwd)
all:
\t$(MAKE) -j$(HOST_NCPU) -C $(SRC_NAME) V=1
clean:
\t$(MAKE) -C $(SRC_NAME) clean
romfs:
\t$(ROMFSINST) $(THISDIR)/$(SRC_NAME)/ip/ip /bin/ip
ifeq ($(CONFIG_FIRMWARE_INCLUDE_SQM),y)
\t$(ROMFSINST) $(THISDIR)/$(SRC_NAME)/tc/tc /bin/tc
endif
'''
prepared = module.prepare(fixture)
assert module.prepare(prepared) == prepared
try:
    module.prepare(fixture.replace('/bin/tc', '/bin/unexpected'))
except ValueError:
    pass
else:
    raise AssertionError('changed upstream packaging was silently accepted')
make = shutil.which('make') or shutil.which('mingw32-make')
if not make:
    raise SystemExit('GNU Make is required to evaluate packaging conditions')
for qos, sqm, expected_tc in [('y', 'n', True), ('n', 'y', True),
                              ('y', 'y', True), ('n', 'n', False),
                              ('', '', False)]:
    result = subprocess.run([make, '--no-print-directory', '-f', '-', '-n', 'romfs',
        'THISDIR=fixture', 'ROMFSINST=install-marker',
        'CONFIG_FIRMWARE_INCLUDE_QOS=' + qos,
        'CONFIG_FIRMWARE_INCLUDE_SQM=' + sqm],
        input=prepared, text=True, capture_output=True, check=True)
    assert ('/tc/tc /bin/tc' in result.stdout) == expected_tc, result.stdout
    assert '/ip/ip /bin/ip' in result.stdout, result.stdout
print('PASS GNU Make installs tc for QoS-only, SQM-only and both; excludes tc with neither; ip and idempotence preserved')
