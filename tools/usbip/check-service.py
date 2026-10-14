#!/usr/bin/env python3
"""Execute candidate lifecycle in an isolated fake process namespace."""
import os
import subprocess
import tempfile
from pathlib import Path

source = Path(__file__).with_name('service.sh').read_text()
with tempfile.TemporaryDirectory(prefix='wr-usbip-service-') as directory:
    root=Path(directory); binary=root/'bin'; binary.mkdir(); proc=root/'proc';proc.mkdir()
    events=root/'events'; pid=root/'daemon.pid'; policy=root/'policy.sh'
    policy.write_text('''wr_usbip_policy_apply() {
 echo "policy:$1" >> "$EVENTS"
 test "${FAIL_POLICY:-0}" = 0
}
wr_usbip_policy_remove() { echo remove-policy >> "$EVENTS"; }
''')
    commands={
        'nvram':'echo br0\n',
        'logger':'echo "log:$*" >> "$EVENTS"\n',
        'modprobe':'echo "module:$*" >> "$EVENTS"\ntest "${FAIL_MODULE:-0}" = 0\n',
        'sleep':':\n',
        'pidof':'for p in "$PROC"/*; do test ! -d "$p" || basename "$p"; done\n',
        'usbipd':'''echo "daemon:$*" >> "$EVENTS"
test "$1" = -4 && test "$2" = -D && test "$3" = "--pid=$PID" || exit 3
test "${FAIL_START:-0}" = 0 || exit 1
mkdir -p "$PROC/234"
ln -s "$DAEMON" "$PROC/234/exe"
printf '234\\n' > "$PID"
''',
        'fixture_signal':'''echo "signal:$*" >> "$EVENTS"
test "$1" = -TERM && test "$2" = 234 || exit 3
test "${STOP_TIMEOUT:-0}" = 0 || exit 0
rm "$PROC/234/exe"
rmdir "$PROC/234"
rm "$PID"
''',
    }
    for name,body in commands.items():
        path=binary/name;path.write_text('#!/bin/sh\n'+body);path.chmod(0o755)
    script=root/'service.sh'
    adapted=source.replace('daemon=/sbin/usbipd','daemon='+str(binary/'usbipd'))
    adapted=adapted.replace('pidfile=/var/run/wr-usbip.pid','pidfile='+str(pid))
    adapted=adapted.replace('policy=/usr/libexec/wr-usbip/firewall-policy.sh','policy='+str(policy))
    adapted=adapted.replace('lock=/var/run/wr-usbip.lock','lock='+str(root/'lock'))
    adapted=adapted.replace('/proc/',str(proc)+'/').replace('kill -TERM','fixture_signal -TERM')
    script.write_text(adapted)
    env=dict(os.environ,PATH=str(binary)+':'+os.environ['PATH'],PROC=str(proc),PID=str(pid),
             EVENTS=str(events),DAEMON=str(binary/'usbipd'))
    def run(action,**extra):
        events.write_text('')
        result=subprocess.run(['sh',str(script),action],env=dict(env,**extra),capture_output=True,text=True)
        return result.returncode,events.read_text()
    rc,trace=run('start',FAIL_POLICY='1');assert rc and 'daemon:' not in trace and 'module:' not in trace
    rc,trace=run('start',FAIL_MODULE='1');assert rc and 'daemon:' not in trace and 'remove-policy' not in trace
    rc,trace=run('start',FAIL_START='1');assert rc and 'remove-policy' not in trace
    rc,trace=run('start');assert rc==0 and trace.index('policy:')<trace.index('module:')<trace.index('daemon:')
    assert run('status')[0]==0
    rc,trace=run('start');assert rc and 'daemon:' not in trace
    rc,trace=run('restart',STOP_TIMEOUT='1');assert rc and 'remove-policy' not in trace and 'daemon:' not in trace
    rc,trace=run('stop');assert rc==0 and trace.index('signal:')<trace.index('remove-policy')
    assert run('status')[0]!=0
    pid.write_text('1\n');rc,trace=run('stop');assert rc and 'signal:' not in trace and 'remove-policy' not in trace
    pid.unlink();(proc/'999').mkdir();(proc/'999/exe').symlink_to('/unrelated')
    rc,trace=run('start');assert rc and 'daemon:' not in trace
    (proc/'999/exe').unlink();(proc/'999').rmdir()
    rc,trace=run('restart');assert rc==0 and trace.index('remove-policy')<trace.index('policy:')
    assert run('stop')[0]==0
print('PASS USB/IP lifecycle: ownership, policy ordering, failed starts, stop timeout and restart guard')
