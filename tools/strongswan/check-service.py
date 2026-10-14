"""Execute the production shell controller against isolated process fixtures."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import uuid

root=Path.cwd()/('sswan-service-check-'+uuid.uuid4().hex);root.mkdir()
try:
    for name in ('bin','proc','run','storage'):(root/name).mkdir()
    def script(name,body):
        target=root/'bin'/name;target.write_text('#!/bin/sh\nset -eu\n'+body);target.chmod(0o755);return target
    script('starter','test "$1" = --conftest; test "$2" = --conf; test -r "$3"; echo checked >> "$SS_ROOT/events"; exit "${SS_CHECK_FAIL:-0}"\n')
    script('charon','exit 0\n')
    script('ipsec',r'''
test "$1" = start; test "$2" = --conf; test -r "$3"
echo start >> "$SS_ROOT/events"
test "${SS_START_FAIL:-0}" = 0 || exit 1
mkdir -p "$SS_ROOT/proc/99991" "$SS_ROOT/proc/99992"
ln -s "$SS_ROOT/bin/starter" "$SS_ROOT/proc/99991/exe"
ln -s "$SS_ROOT/bin/charon" "$SS_ROOT/proc/99992/exe"
echo 99991 > "$SS_ROOT/run/starter.charon.pid"
echo 99992 > "$SS_ROOT/run/charon.pid"
echo '99991 99992' > "$SS_ROOT/running"
''')
    script('pidof','test -f "$SS_ROOT/running" && cat "$SS_ROOT/running"\n')
    script('flock','exit "${SS_LOCK_FAIL:-0}"\n')
    script('logger','echo refusal >> "$SS_ROOT/events"\n')
    script('sleep','exit 0\n')
    script('stop',r'''
echo stop >> "$SS_ROOT/events"
test "${SS_STOP_TIMEOUT:-0}" = 0 || exit 0
rm -f "$SS_ROOT/proc/99991/exe" "$SS_ROOT/proc/99992/exe"
rmdir "$SS_ROOT/proc/99991" "$SS_ROOT/proc/99992"
rm -f "$SS_ROOT/run/starter.charon.pid" "$SS_ROOT/run/charon.pid" "$SS_ROOT/running"
''')
    source=Path(__file__).with_name('strongswan-service.sh').read_text()
    for key,value in {'ipsec':root/'bin/ipsec','starter':root/'bin/starter','charon':root/'bin/charon','config':root/'storage/ipsec.conf','starter_pid':root/'run/starter.charon.pid','charon_pid':root/'run/charon.pid','lock':root/'run/lock'}.items():
        source='\n'.join(key+'='+shlex.quote(str(value)) if line.startswith(key+'=') else line for line in source.split('\n'))
    source=source.replace('/proc/',str(root/'proc')+'/')
    controller=root/'controller.sh'
    controller.write_text('kill(){ test "$1" = -TERM; test "$2" = 99991; "$SS_ROOT/bin/stop"; }\n'+source)
    config=root/'storage/ipsec.conf';config.write_text('config setup\n# preserved profile fixture\n')
    original=config.read_bytes()
    def run(action,ok,**extra):
        result=subprocess.run(['sh',str(controller),*action],env={**os.environ,'SS_ROOT':str(root),'PATH':str(root/'bin')+':'+os.environ['PATH'],**extra},capture_output=True,text=True,timeout=5)
        assert (result.returncode==0)==ok,(action,result.returncode,result.stderr)
        assert config.read_bytes()==original
    run(['check'],True);run(['status'],False)
    run(['start'],False,SS_CHECK_FAIL='1');assert not (root/'running').exists()
    run(['start'],False,SS_START_FAIL='1');assert not (root/'running').exists()
    run(['start'],False,SS_LOCK_FAIL='1');assert not (root/'running').exists()
    run(['start'],True);run(['status'],True);run(['start'],False)
    before=(root/'events').read_text().count('start\n')
    run(['restart'],False,SS_STOP_TIMEOUT='1');assert (root/'events').read_text().count('start\n')==before
    run(['restart'],True);run(['stop'],True);run(['stop'],True)
    (root/'run/starter.charon.pid').write_text('1\n');run(['stop'],False)
    (root/'run/starter.charon.pid').unlink();(root/'running').write_text('54321\n');run(['start'],False)
    run(['start','unexpected'],False);run(['unknown'],False)
finally:
    assert root.resolve().parent==Path.cwd().resolve()
    shutil.rmtree(root)
print('PASS StrongSwan controller preflight, ownership refusal, start/stop/restart, timeout and config preservation; isolated mocked processes only')
