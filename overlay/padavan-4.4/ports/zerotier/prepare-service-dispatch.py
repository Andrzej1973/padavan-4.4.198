#!/usr/bin/env python3
"""Preserve action failures and apply explicit leave even with service disabled."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
service = root / 'trunk/user/rc/services.c'
s = service.read_text(encoding='utf-8')
old = '''void restart_zerotier(void){
	stop_zerotier();
	start_zerotier();
}'''
new = '''void restart_zerotier(void){
	if (eval("/usr/bin/zerotier.sh", "stop") != 0) {
		logmessage("ZeroTier", "Service stop failed; restart deferred");
		return;
	}
	if (eval("/usr/bin/zerotier.sh", "sync") != 0) {
		logmessage("ZeroTier", "Network membership update failed; restart deferred");
		return;
	}
	start_zerotier();
}'''
if s.count(old) != 1:
    raise SystemExit('Pinned ZeroTier service dispatch mismatch')
s = s.replace(old, new)
script = root / 'trunk/user/zerotier/zerotier.sh'
sh = script.read_text(encoding='utf-8')
allowed = 'case "$1" in start|stop|refresh)'
dispatch = 'case $1 in\nrefresh)'
if sh.count(allowed) != 1 or sh.count(dispatch) != 1:
    raise SystemExit('Prepared ZeroTier shell dispatch mismatch')
sh = sh.replace(allowed, 'case "$1" in start|stop|refresh|sync)').replace(
    'Usage: zerotier.sh start|stop|refresh', 'Usage: zerotier.sh start|stop|refresh|sync')
sh = sh.replace(dispatch, '''case $1 in
sync)
	# Config file updates are safe only after a successful service stop.
	for zerotier_process in $(pidof zerotier-one); do
		is_zerotier_pid "$zerotier_process" && exit 1
	done
	mkdir -p "$config_path/networks.d" || exit 1
	add_join "$(nvram get zerotier_id)" || exit 1
	;;
refresh)''')
for path, text in ((service, s), (script, sh)):
    with path.open('w', encoding='utf-8', newline='\n') as out:
        out.write(text)
print('ZeroTier restart failure handling and disabled-service membership updates integrated')
