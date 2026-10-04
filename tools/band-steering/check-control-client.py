"""Real host client/server IPC check. Requires root in isolated CI, not a router."""
import os, subprocess, sys
from pathlib import Path
client, server, directory = sys.argv[1:]
assert os.geteuid() == 0
def invoke(*commands):
    return subprocess.run([client, *commands], capture_output=True, text=True, timeout=4)
missing = invoke('status')
assert missing.returncode == 1 and not missing.stdout and 'unverified' in missing.stderr
p = subprocess.Popen([server, str(Path(directory)/'control')], stdout=subprocess.PIPE, text=True)
try:
    import select
    assert select.select([p.stdout], [], [], 3)[0], 'server readiness timeout'
    assert p.stdout.readline() == 'READY\n'
    active = invoke('status')
    assert active.returncode == 0 and active.stdout == 'active\n', active
    owned = invoke('status-pid', str(p.pid))
    assert owned.returncode == 0 and owned.stdout == 'active\n', owned
    ready = invoke('ready-pid', str(p.pid))
    assert ready.returncode == 0 and ready.stdout == 'active\n', ready
    wrong_ready = invoke('ready-pid', str(p.pid + 1))
    assert wrong_ready.returncode == 1 and not wrong_ready.stdout, wrong_ready
    other = invoke('status-pid', str(p.pid + 1))
    assert other.returncode == 1 and not other.stdout and 'unverified' in other.stderr, other
    for bad in ('0', '1', '-1', '+2', '2x', '', '999999999999999999999999999'):
        invalid_pid = invoke('status-pid', bad)
        assert invalid_pid.returncode == 2 and not invalid_pid.stdout, invalid_pid
    invalid = invoke('invalid')
    assert invalid.returncode == 2 and not invalid.stdout
    stop = invoke('stop')
    assert stop.returncode == 0 and stop.stdout == 'stop_requested_off_unverified\n', stop
    assert p.wait(timeout=3) == 0
    assert not (Path(directory)/'control').exists()
    assert invoke('status').returncode == 1
finally:
    if p.poll() is None: p.kill(); p.wait()
p = subprocess.Popen([server, str(Path(directory)/'control'), 'querying'], stdout=subprocess.PIPE, text=True)
try:
    assert select.select([p.stdout], [], [], 3)[0], 'querying server readiness timeout'
    assert p.stdout.readline() == 'READY\n'
    phase = invoke('status-pid', str(p.pid))
    assert phase.returncode == 0 and phase.stdout == 'querying\n', phase
    not_ready = invoke('ready-pid', str(p.pid))
    assert not_ready.returncode == 1 and not not_ready.stdout, not_ready
    assert invoke('stop').returncode == 0
    assert p.wait(timeout=3) == 0
finally:
    if p.poll() is None: p.kill(); p.wait()
print('PASS actual local client/server status, expected daemon PID, ACTIVE readiness and stop acknowledgement; radio behavior unverified')
