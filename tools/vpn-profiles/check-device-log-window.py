#!/usr/bin/env python3
"""Ensure rotated/missing journals cannot pass the post-flash noise check."""
import os
from pathlib import Path
import subprocess
import tempfile

script = Path(__file__).with_name('check-device-readonly.sh').resolve()
with tempfile.TemporaryDirectory(prefix='wr-log-window-') as directory:
    root = Path(directory)
    log = root / 'syslog.log'
    sleep = root / 'sleep'
    sleep.write_text('''#!/bin/sh
case "$WR_LOG_ACTION" in
  append) printf '%s\\n' "$WR_LOG_APPEND" >> "$WR_LOG_FILE" ;;
  rotate) printf '%s\\n' "$WR_LOG_APPEND" > "$WR_LOG_FILE" ;;
  delete) rm -f "$WR_LOG_FILE" ;;
  fail) exit 1 ;;
esac
''')
    sleep.chmod(0o700)
    cases = [
        ('missing', None, 'append', 'normal', 2),
        ('empty', '', 'append', 'normal', 2),
        ('unchanged', 'old Reaped\nunique cursor\n', '', '', 0),
        ('quiet-append', 'old BndStrg_InfStatusRsp\nunique cursor\n', 'append', 'normal event', 0),
        ('status-noise', 'unique cursor\n', 'append', 'new BndStrg_InfStatusRsp', 1),
        ('reaper-noise', 'unique cursor\n', 'append', 'new Reaped child', 1),
        ('rotation', 'old BndStrg_InfStatusRsp\nunique cursor\n', 'rotate', 'new BndStrg_InfStatusRsp', 2),
        ('ambiguous', 'duplicate\nduplicate\n', '', '', 2),
        ('deleted', 'unique cursor\n', 'delete', '', 2),
        ('wait-failure', 'unique cursor\n', 'fail', '', 2),
    ]
    for name, before, action, appended, expected in cases:
        log.unlink(missing_ok=True)
        if before is not None:
            log.write_text(before)
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                   WR_LOG_ACTION=action, WR_LOG_APPEND=appended, WR_LOG_FILE=str(log))
        result = subprocess.run(['sh', str(script), '--log-window', str(log)],
                                capture_output=True, text=True, env=env, timeout=5)
        assert result.returncode == expected, (name, result.returncode, result.stdout, result.stderr)
        assert result.stdout.startswith({0: 'PASS ', 1: 'FAIL ', 2: 'UNKNOWN '}[expected]), name
        assert not result.stderr
    print('PASS post-flash journal window: missing/rotation/ambiguity/read/wait failures stay unknown; only new noise fails')
