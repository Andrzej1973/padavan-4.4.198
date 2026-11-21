#!/usr/bin/env python3
"""Exercise the shipped ZeroTier persistence hash with exact-image BusyBox.

Only synthetic files and a mocked storage-save function are used. This does
not run the daemon, access flash or establish router runtime acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('romfs', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.romfs.resolve()
busybox = root / 'bin/busybox'
lifecycle = root / 'usr/bin/zerotier.sh'
qemu = shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
if not qemu or not busybox.is_file() or not lifecycle.is_file():
    raise SystemExit('Target QEMU, BusyBox and shipped ZeroTier helper are required')
source = lifecycle.read_text(encoding='utf-8')
start = source.index('persistent_state_hash() {')
end = source.index('start_instance() {', start)
functions = source[start:end]
functions, replacements = re.subn(
    r'for state_file in .*?; do', 'for state_file in "$FIXTURE_FILE"; do',
    functions, count=1, flags=re.S)
if replacements != 1 or functions.count('/var/run/zerotier-storage-pending') != 4:
    raise SystemExit('Unexpected shipped ZeroTier persistence helper structure')
functions = functions.replace('/var/run/zerotier-storage-pending', '"$PENDING_FILE"')
if functions.count('/sbin/mtd_storage.sh save') != 1:
    raise SystemExit('Unexpected shipped ZeroTier storage-save call')
functions = functions.replace('/sbin/mtd_storage.sh save', 'save_storage')

shell = [qemu, '-L', str(root), str(busybox)]
inventory = subprocess.run([*shell, '--list'], capture_output=True, text=True, timeout=15)
required = {'md5sum', 'sort', 'rm', 'cat'}
missing = required - set(inventory.stdout.splitlines())
if inventory.returncode or missing:
    raise SystemExit('Missing target BusyBox applets: ' + ', '.join(sorted(missing)))

prelude = r'''logger() { :; }
save_storage() {
    printf 'save\n' >> "$EVENTS"
    [ "${SAVE_FAIL:-0}" != 1 ]
}
md5sum() {
    if [ "${FAIL:-none}" = file ] && [ "${1:-}" = "$FIXTURE_FILE" ]; then return 9; fi
    if [ "${FAIL:-none}" = aggregate ] && [ "$#" -eq 0 ]; then return 9; fi
    "$PROVIDERS/md5sum" "$@"
}
sort() {
    if [ "${FAIL:-none}" = sort ]; then return 9; fi
    "$PROVIDERS/sort" "$@"
}
'''
cases = r'''
state_before=$(persistent_state_hash) || exit 91
case "$SCENARIO" in
    unchanged)
        persist_state_if_changed || exit 1
        [ ! -f "$PENDING_FILE" ] && [ ! -s "$EVENTS" ] ;;
    changed)
        printf 'changed\n' > "$FIXTURE_FILE"
        persist_state_if_changed || exit 1
        [ ! -f "$PENDING_FILE" ] && [ "$(cat "$EVENTS")" = save ] ;;
    file_failure|aggregate_failure|sort_failure)
        FAIL=${SCENARIO%_failure}
        if persist_state_if_changed; then exit 1; fi
        [ -f "$PENDING_FILE" ] && [ ! -s "$EVENTS" ] || exit 1
        FAIL=none
        persist_state_if_changed || exit 1
        [ ! -f "$PENDING_FILE" ] && [ "$(cat "$EVENTS")" = save ] ;;
    save_failure)
        printf 'changed\n' > "$FIXTURE_FILE"
        SAVE_FAIL=1
        if persist_state_if_changed; then exit 1; fi
        [ -f "$PENDING_FILE" ] || exit 1
        SAVE_FAIL=0
        persist_state_if_changed || exit 1
        [ ! -f "$PENDING_FILE" ] && [ "$(cat "$EVENTS")" = "$(printf 'save\nsave')" ] ;;
    *) exit 2 ;;
esac
'''

checks = {}
with tempfile.TemporaryDirectory(prefix='zt-hash-target-') as directory:
    work = Path(directory)
    providers = work / 'providers'
    providers.mkdir()
    for applet in sorted(required):
        wrapper = providers / applet
        wrapper.write_text('#!/bin/sh\nexec ' + shlex.join([*shell, applet]) + ' "$@"\n')
        wrapper.chmod(0o700)
    fixture = work / 'identity.secret'
    events = work / 'events'
    pending = work / 'storage-pending'
    script = work / 'probe.sh'
    script.write_text(prelude + functions + cases, encoding='utf-8')
    environment = dict(os.environ, PATH=str(providers), PROVIDERS=str(providers),
                       FIXTURE_FILE=str(fixture), PENDING_FILE=str(pending),
                       EVENTS=str(events), LC_ALL='C')
    for case in ('unchanged', 'changed', 'file_failure',
                 'aggregate_failure', 'sort_failure', 'save_failure'):
        fixture.write_text('original\n', encoding='utf-8')
        events.write_text('', encoding='utf-8')
        pending.unlink(missing_ok=True)
        result = subprocess.run([*shell, 'sh', str(script)],
                                env=dict(environment, SCENARIO=case),
                                capture_output=True, text=True, timeout=30)
        checks[case] = result.returncode == 0
        if not checks[case]:
            checks[case + '_stderr'] = result.stderr[-1000:]

report = {'scope': 'exact-image BusyBox/QEMU with synthetic ZeroTier files and mocked storage save',
          'busybox_sha256': hashlib.sha256(busybox.read_bytes()).hexdigest(),
          'lifecycle_sha256': hashlib.sha256(lifecycle.read_bytes()).hexdigest(),
          'checks': checks, 'router_runtime_verified': False}
args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
if not all(checks.get(case) for case in ('unchanged', 'changed', 'file_failure',
                                        'aggregate_failure', 'sort_failure',
                                        'save_failure')):
    raise SystemExit('ZeroTier target persistence hash fixture failed')
print('PASS ZeroTier exact-image BusyBox persistence hash fixture')
