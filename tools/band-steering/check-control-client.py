"""Real host client/server IPC check. Requires root in isolated CI, not a router."""
import os, subprocess, sys
from pathlib import Path
client, server, directory = sys.argv[1:]
assert os.geteuid() == 0
def invoke(command):
    return subprocess.run([client, command], capture_output=True, text=True, timeout=4)
missing = invoke('status')
assert missing.returncode == 1 and not missing.stdout and 'unverified' in missing.stderr
p = subprocess.Popen([server, str(Path(directory)/'control')], stdout=subprocess.PIPE, text=True)
try:
    import select
    assert select.select([p.stdout], [], [], 3)[0], 'server readiness timeout'
    assert p.stdout.readline() == 'READY\n'
    active = invoke('status')
    assert active.returncode == 0 and active.stdout == 'active\n', active
    invalid = invoke('invalid')
    assert invalid.returncode == 2 and not invalid.stdout
    stop = invoke('stop')
    assert stop.returncode == 0 and stop.stdout == 'stop_requested_off_unverified\n', stop
    assert p.wait(timeout=3) == 0
    assert not (Path(directory)/'control').exists()
    assert invoke('status').returncode == 1
finally:
    if p.poll() is None: p.kill(); p.wait()
print('PASS actual local client/server status and stop acknowledgement; radio behavior unverified')
