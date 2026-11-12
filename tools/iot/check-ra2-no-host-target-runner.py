#!/usr/bin/env python3
"""Regress experimental include mapping and excluded-branch refusal."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
runner = here / 'check-ra2-no-host-target-units.py'
tree = ast.parse(runner.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == 'remap_driver_argument')
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), 'actual-remapper', 'exec'), namespace)
remap = namespace[function.name]
for value, expected in (
        ('-Idrivers/mt76x3', '-I/tmp/experiment'),
        ('-I/target/drivers/mt76x3', '-I/tmp/experiment'),
        ('-Idrivers/mt76x3/include', '-I/tmp/experiment/include'),
        ('drivers/mt76x3', '/tmp/experiment'),
        ('-iquotedrivers/mt76x3', '-iquote/tmp/experiment'),
        ('-Iinclude', '-Iinclude'),
        ('-Idrivers/mt76x3_other', '-Idrivers/mt76x3_other')):
    assert remap(value, Path('/target/drivers/mt76x3'), 'drivers/mt76x3', Path('/tmp/experiment')) == expected
with tempfile.TemporaryDirectory(prefix='wr-ra2-target-runner-') as scratch:
    root = Path(scratch)
    kernel = root / 'kernel'
    driver = kernel / 'driver'
    experiment = root / 'experiment'
    output = root / 'results'
    (driver / 'mac').mkdir(parents=True)
    (experiment / 'mac').mkdir(parents=True)
    config = b'CONFIG_TEST=y\n'
    (kernel / '.config').write_bytes(config)
    (driver / 'mac/mt_mac.c').write_text('int baseline;\n')
    (experiment / 'mac/mt_mac.c').write_text('int experimental;\n')
    compiler = Path(shutil.which('gcc')).resolve()
    (driver / 'mac/.mt_mac.o.cmd').write_text(
        'cmd_test := ' + str(compiler) + ' -c -o driver/mac/mt_mac.o driver/mac/mt_mac.c\n')
    manifest = Path(str(experiment) + '.manifest.json')
    hashes = {'mac/mt_mac.c': hashlib.sha256((experiment / 'mac/mt_mac.c').read_bytes()).hexdigest()}
    arguments = [sys.executable, '-B', str(runner), '--kernel', str(kernel),
                 '--driver', str(driver), '--experiment', str(experiment),
                 '--compiler', str(compiler), '--output', str(output)]
    for recorded, expected in (({}, 'source identity mismatch'), (hashes, 'branches excluded')):
        manifest.write_text(json.dumps({'candidate_driver_sha256': recorded,
                                       'ra2_no_host_experiment': {'activation_ready': False}}))
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=30)
        report = json.loads((output / 'report.json').read_text())
        assert result.returncode and expected in report['error'] and not report['units']
        assert (kernel / '.config').read_bytes() == config
    assert (output / 'mac_mt_mac.c.macros.txt').is_file()
print('PASS target runner root/nested include mapping, manifest refusal and actual excluded-branch preprocessing refusal')
