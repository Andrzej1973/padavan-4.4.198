#!/usr/bin/env python3
"""Apply first persistence/process fixes to pinned Padavan ZeroTier lifecycle.

Network/firewall policy and the expanded WebUI are separate pending work.
Existing moon, custom planet and static route features remain present.
"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
path = args.source / 'trunk/user/zerotier/zerotier.sh'
text = path.read_text(encoding='utf-8')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise SystemExit('Pinned ZeroTier lifecycle anchor mismatch: ' + repr(old[:80]))
    text = text.replace(old, new)

replace_once('\tsecret="$(nvram get zerotier_secret)"\n', '''\tsecret="$(nvram get zerotier_secret)"
	# Existing persistent identity takes precedence over legacy NVRAM storage.
	if [ -s "$config_path/identity.secret" ]; then
		secret="$(cat "$config_path/identity.secret")"
	fi
''')
replace_once('add_join() {\n\t\ttouch $config_path/networks.d/$1.conf\n}', '''add_join() {
	# A blank Network ID is allowed for an enabled, not-yet-joined node.
	[ -z "$1" ] && return 0
	[ "${#1}" -eq 16 ] || return 1
	case "$1" in *[!0-9a-fA-F]*) return 1 ;; esac
	touch "$config_path/networks.d/$1.conf"
}''')
replace_once('\tadd_join $(nvram get zerotier_id)\n', '''	add_join "$(nvram get zerotier_id)" || {
		logger -t zerotier "Invalid Network ID; startup rejected"
		return 1
	}
''')
old = '''kill_z() {
	zerotier_process=$(pidof zerotier-one)
	if [ -n "$zerotier_process" ]; then
		logger -t "zerotier" "关闭进程..."
		killall zerotier-one >/dev/null 2>&1
		kill -9 "$zerotier_process" >/dev/null 2>&1
	fi
}'''
new = '''is_zerotier_pid() {
	case "$1" in ''|*[!0-9]*) return 1 ;; esac
	[ "$(readlink "/proc/$1/exe" 2>/dev/null)" = "$PROG" ]
}
kill_z() {
	for zerotier_process in $(pidof zerotier-one); do
		is_zerotier_pid "$zerotier_process" || continue
		kill -TERM "$zerotier_process" 2>/dev/null || continue
		attempt=0
		while is_zerotier_pid "$zerotier_process" && [ "$attempt" -lt 8 ]; do
			sleep 1
			attempt=$((attempt + 1))
		done
		# Recheck ownership before a bounded forced-stop fallback.
		if is_zerotier_pid "$zerotier_process"; then
			logger -t zerotier "Graceful stop timed out; terminating daemon"
			kill -KILL "$zerotier_process" 2>/dev/null
		fi
	done
}'''
replace_once(old, new)
replace_once('\trm -rf $config_path\n', '''	# Keep identity, membership, moons and custom planet on stop/restart.
''')
# Cache dropping is unrelated to the service and affects all router workloads.
if text.count('        echo 3 > /proc/sys/vm/drop_caches\n') != 2:
    raise SystemExit('Pinned ZeroTier cache-drop anchor mismatch')
text = text.replace('        echo 3 > /proc/sys/vm/drop_caches\n', '')
with path.open('w', encoding='utf-8', newline='\n') as output:
    output.write(text)
print('ZeroTier identity/membership preserved; Network ID and daemon stop guarded.')

