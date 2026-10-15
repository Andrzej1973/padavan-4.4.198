#!/usr/bin/env python3
"""Offline shell-policy checks; no real NVRAM, module or netlink operations."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-eoip-policy-') as directory:
    root = Path(directory)
    log = root / 'calls'
    helper = root / 'helper'
    helper.write_text('''#!/usr/bin/env python3
import json, os, sys
name = os.path.basename(sys.argv[0])
with open(os.environ['EOIP_TEST_LOG'], 'a') as out:
    out.write(json.dumps([name] + sys.argv[1:]) + '\\n')
if name == 'nvram':
    key = sys.argv[2]
    if key == os.environ.get('EOIP_TEST_FAIL_KEY'): sys.exit(1)
    print(json.loads(os.environ['EOIP_TEST_VALUES']).get(key, ''))
elif name == 'modprobe':
    sys.exit(int(os.environ.get('EOIP_TEST_MODULE_EXIT', '0')))
''')
    helper.chmod(0o755)
    for name in ('nvram', 'modprobe', 'worker'):
        (root / name).symlink_to(helper)
    # Only redirect the hard-coded worker path in this isolated copy. PATH
    # supplies mocked nvram/modprobe; the production script is not modified.
    script = root / 'policy.sh'
    script.write_text((HERE / 'boot.sh').read_text().replace(
        '/usr/bin/eoip-service', str(root / 'worker')))

    def run(action, values, fail_key='', module_exit=0):
        log.write_text('')
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                   EOIP_TEST_LOG=str(log), EOIP_TEST_VALUES=json.dumps(values),
                   EOIP_TEST_FAIL_KEY=fail_key, EOIP_TEST_MODULE_EXIT=str(module_exit))
        result = subprocess.run(['/bin/sh', str(script), action], env=env, cwd=root,
                                capture_output=True, text=True, timeout=15)
        return result.returncode, [json.loads(line) for line in log.read_text().splitlines()]

    code, calls = run('boot', {'eoip_enable': '0'})
    assert code == 0 and calls == [['nvram', 'get', 'eoip_enable']]
    code, calls = run('stop', {})
    assert code == 0 and calls == [['worker', 'stop-table']]
    code, calls = run('apply', {'eoip_enable': '0'})
    assert code == 0 and calls[-1] == ['worker', 'stop-table']
    code, calls = run('apply', {'eoip_enable': 'bad'})
    assert code == 65 and all(call[0] == 'nvram' for call in calls)
    code, calls = run('boot', {}, fail_key='eoip_enable')
    assert code == 67 and len(calls) == 1

    values = {'eoip_enable': '1'}
    for slot in range(8):
        fields = dict(enable='0', autostart='0', local='0.0.0.0', remote='',
                      id='0', mtu='1458', keepalive='0', retries='0', bridge='')
        values.update({f'eoip_slot{slot}_{key}': value for key, value in fields.items()})
    # Invalid content must arrive as one literal argument for the C validator;
    # no shell interpolation or command substitution may execute it.
    values['eoip_slot0_bridge'] = 'br0;$(touch SHOULD_NOT_EXIST)'
    for action, command in [('boot', 'boot-table'), ('apply', 'apply-table')]:
        code, calls = run(action, values)
        assert code == 0
        assert calls[-2] == ['modprobe', 'eoip']
        args = calls[-1]
        assert args[:2] == ['worker', command] and len(args) == 82
        assert args[11] == values['eoip_slot0_bridge']
        assert args[72] == '7'
        assert not (root / 'SHOULD_NOT_EXIST').exists()
    code, calls = run('apply', values, fail_key='eoip_slot7_bridge')
    assert code == 67 and all(call[0] == 'nvram' for call in calls)
    code, calls = run('apply', values, module_exit=1)
    assert code == 67 and calls[-1] == ['modprobe', 'eoip']
    assert not any(call[0] == 'worker' for call in calls)
print('PASS EoIP shell policy: default-off, profile-independent stop, full quoted snapshot, failures')
