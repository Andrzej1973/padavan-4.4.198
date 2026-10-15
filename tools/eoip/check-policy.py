#!/usr/bin/env python3
"""Check shell dispatch only; NVRAM/locking tests are native check-stored.c."""
import os
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='wr-eoip-policy-') as directory:
    root = Path(directory)
    worker = root / 'worker'
    worker.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$EOIP_TEST_LOG"\nexit "${EOIP_TEST_EXIT:-0}"\n')
    worker.chmod(0o755)
    script = root / 'policy'
    script.write_text(Path(__file__).with_name('boot.sh').read_text().replace('/usr/bin/eoip-service', str(worker)))
    log = root / 'calls'
    for action, command in [('boot', 'boot-stored'), ('apply', 'apply-stored'), ('stop', 'stop-table')]:
        env = dict(os.environ, EOIP_TEST_LOG=str(log))
        result = subprocess.run(['/bin/sh', str(script), action], env=env, timeout=5)
        assert result.returncode == 0 and log.read_text().splitlines() == [command]
        env['EOIP_TEST_EXIT'] = '67'
        assert subprocess.run(['/bin/sh', str(script), action], env=env, timeout=5).returncode == 67
    assert subprocess.run(['/bin/sh', str(script), 'invalid'], capture_output=True, timeout=5).returncode == 64
print('PASS EoIP shell dispatch: fixed arguments, direct exec and exit code propagation')
