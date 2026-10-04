#!/usr/bin/env python3
"""Stage bounded serialization of existing ZeroTier lifecycle commands."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
script = p.parse_args().source / 'trunk/user/zerotier/zerotier.sh'
text = script.read_text(encoding='utf-8')
anchor = 'case $1 in\nstart)'
guard = '''# Serialize service actions without requiring BusyBox flock -w support.
case "$1" in start|stop) ;; *) echo "Usage: zerotier.sh start|stop" >&2; exit 2 ;; esac
mkdir -p /var/run || exit 1
exec 9> /var/run/zerotier-action.lock || exit 1
action_attempt=0
while ! flock -n 9; do
	[ "$action_attempt" -lt 10 ] || {
		logger -t zerotier "Service action busy; retry required"
		exit 75
	}
	sleep 1
	action_attempt=$((action_attempt + 1))
done

'''
spawn = '\t$PROG $args $config_path >/dev/null 2>&1 &'
if text.count(anchor) != 1 or text.count(spawn) != 1:
    raise SystemExit('Pinned ZeroTier action/daemon anchors mismatch')
text = text.replace(anchor, guard + anchor).replace(
    spawn, '\t# The daemon must not retain the service action lock.\n'
    '\t$PROG $args "$config_path" >/dev/null 2>&1 9>&- &')
# Propagate action failure; the legacy trailing sleep otherwise masks it.
for action in ('start_zero', 'stop_zero'):
    dispatch = '\t' + action + '\n\tsleep 2'
    if text.count(dispatch) != 1:
        raise SystemExit('Pinned service dispatch anchor mismatch: ' + action)
    text = text.replace(dispatch, '\t' + action + ' || exit $?\n\tsleep 2')
with script.open('w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print('Staged bounded service action lock and daemon fd closure')
