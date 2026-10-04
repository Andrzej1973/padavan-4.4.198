#!/usr/bin/env python3
"""Stage saves on persistent ZeroTier changes, with retry after failed save."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
script = p.parse_args().source / 'trunk/user/zerotier/zerotier.sh'
s = script.read_text(encoding='utf-8')
helper = r'''persistent_state_hash() {
	# Explicit durable files only: peer cache, PID, port and status are excluded.
	for state_file in "$config_path/identity.secret" "$config_path/identity.public" \
		"$config_path/local.conf" "$config_path/planet" "$config_path/moon.json" \
		"$config_path/web-managed-network" "$config_path"/networks.d/*.conf \
		"$config_path"/moons.d/*.moon; do
		[ ! -f "$state_file" ] || md5sum "$state_file"
	done | sort | md5sum | awk '{print $1}'
}
persist_state_if_changed() {
	state_after=$(persistent_state_hash)
	if [ "$state_before" != "$state_after" ] || [ -f /var/run/zerotier-storage-pending ]; then
		: > /var/run/zerotier-storage-pending || return 1
		if ! /sbin/mtd_storage.sh save >/dev/null 2>&1; then
			logger -t zerotier "Persistent storage save failed; retry required before service start"
			return 1
		fi
		rm -f /var/run/zerotier-storage-pending
	fi
	return 0
}

'''
anchor = 'start_instance() {\n'
if s.count(anchor) != 1:
    raise SystemExit('Prepared ZeroTier startup anchor mismatch')
s = s.replace(anchor, helper + anchor + '\tstate_before=$(persistent_state_hash)\n')
# Moon generation uses local identity files and idtool, not a running daemon.
start = s.index('\tif [ -n "$enablemoonserv" ]; then')
end = s.index('\n}\n', start)
moon = s[start:end]
s = s[:start] + s[end:]
anchor = '\t# Install scoped rules before any overlay interface can appear.'
if s.count(anchor) != 1:
    raise SystemExit('Prepared ZeroTier policy anchor mismatch')
s = s.replace(anchor, moon + '\n\tpersist_state_if_changed || return 1\n\n' + anchor)
anchor = '\tmkdir -p "$config_path/networks.d" || exit 1\n\tadd_join "$(nvram get zerotier_id)" || exit 1\n'
if s.count(anchor) != 1:
    raise SystemExit('Prepared explicit membership sync anchor mismatch')
s = s.replace(anchor, '\tstate_before=$(persistent_state_hash)\n' + anchor +
              '\tpersist_state_if_changed || exit 1\n')
with script.open('w', encoding='utf-8', newline='\n') as out:
    out.write(s)
print('Staged durable-change saves before daemon start and explicit membership sync')
