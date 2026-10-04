#!/usr/bin/env python3
"""Stage persistent archives without ZeroTier peer cache or premature hash commit."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
path = p.parse_args().source / 'trunk/user/scripts/mtd_storage.sh'
s = path.read_text(encoding='utf-8')
old = '\tfind * ! -type d -print0 | sort -z | xargs -0 tar -cf $tmp 2>/dev/null'
new = '''	# Peer cache and daemon PID/port files are rebuilt by ZeroTier on startup.
	# Keep identity, network configuration, local.conf, moons and custom planet.
	find * \\( -path 'zerotier-one/peers.d' -o \
		-path 'zerotier-one/zerotier-one.pid' -o \
		-path 'zerotier-one/zerotier-one.port' \\) -prune -o \
		! -type d -print0 | sort -z | xargs -0 tar -cf $tmp 2>/dev/null'''
if s.count(old) != 1:
    raise SystemExit('Pinned archive enumeration anchor mismatch')
s = s.replace(old, new)
# Only the save function changes. The load function still records loaded data.
start = s.index('func_save()\n{'); end = s.index('\nfunc_backup()', start)
body = s[start:end]
old_hash = '\tmd5sum $tmp > $hsh\n'
success = '\t\t\techo "Done."'
cleanup = '\trm -f $tmp\n\trm -f $tbz\n'
if body.count(old_hash) != 1 or body.count(success) != 1 or body.count(cleanup) != 1:
    raise SystemExit('Pinned storage save transaction anchors mismatch')
body = body.replace(old_hash, '\tmd5sum $tmp > "${hsh}.new" || { result=1; return 1; }\n')
body = body.replace(success, '\t\t\tmv -f "${hsh}.new" "$hsh" || result=1\n' + success)
body = body.replace(cleanup, '\trm -f "${hsh}.new"\n' + cleanup)
s = s[:start] + body + s[end:]
# Serialize archive construction and flash access across all storage commands.
# flock has no -w option in this BusyBox; retry explicitly with a deadline.
anchor = 'case "$1" in\nload)'
guard = '''mkdir -p /var/run || exit 1
exec 7> /var/run/storage-transaction.lock || exit 1
storage_attempt=0
while ! flock -n 7; do
    [ "$storage_attempt" -lt 30 ] || {
        logger -t Storage "Storage transaction busy; retry required"
        exit 75
    }
    sleep 1
    storage_attempt=$((storage_attempt + 1))
done

'''
if s.count(anchor) != 1 or s.count('\t/sbin/rstats\n') != 1:
    raise SystemExit('Pinned storage transaction anchors mismatch')
s = s.replace(anchor, guard + anchor).replace('\t/sbin/rstats\n', '\t/sbin/rstats 7>&-\n')
with path.open('w', encoding='utf-8', newline='\n') as out:
    out.write(s)
print('Staged ZeroTier cache exclusion and storage hash commit after successful flash write')
