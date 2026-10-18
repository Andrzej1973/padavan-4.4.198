#!/usr/bin/env python3
"""Restore private profile-directory mode after file-only storage extraction."""
import argparse
from pathlib import Path

HELPER = r'''
# WR private VPN profile directory: file-only archives omit directory modes.
func_wrvpn_private()
{
    local profile_dir="$1/wrvpn"
    [ ! -L "$profile_dir" ] || return 1
    [ -e "$profile_dir" ] || return 0
    [ -d "$profile_dir" ] || return 1
    chmod 700 "$profile_dir"
}
'''
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
path = a.source / ('trunk/romfs/sbin/mtd_storage.sh' if a.verify_image else 'trunk/user/scripts/mtd_storage.sh')
s = path.read_text(encoding='utf-8')
if a.verify_image:
    if HELPER.strip() not in s or s.count('func_wrvpn_private "$dir_storage"') != 2:
        raise SystemExit('VPN storage private-directory repair missing in image')
    print('PASS VPN directory mode repair present on storage load and restore; physical persistence unverified')
else:
    load = '\t\ttar xf $tmp -C $dir_storage 2>/dev/null\n'
    restore = '\tcp -rf $tmp_storage /etc\n'
    anchor = 'func_load()\n'
    if s.count(load) != 1 or s.count(restore) != 1 or s.count(anchor) != 1 or 'func_wrvpn_private' in s:
        raise SystemExit('Pinned storage load/restore anchors changed')
    s = s.replace(anchor, HELPER + '\n' + anchor, 1)
    s = s.replace(load, '\t\tif ! tar xf $tmp -C $dir_storage 2>/dev/null || ! func_wrvpn_private "$dir_storage"; then\n'
                  '\t\t\tresult=1\n\t\t\trm -f "$hsh"\n'
                  '\t\t\tlogger -t "Storage load" "Storage extraction or VPN directory permissions failed"\n\t\tfi\n', 1)
    s = s.replace(restore, restore + '\tif ! func_wrvpn_private "$dir_storage"; then\n'
                  '\t\tresult=1\n\t\trm -rf "$tmp_storage"\n'
                  '\t\tlogger -t "Storage restore" "VPN directory permissions failed"\n\t\treturn 1\n\tfi\n', 1)
    path.write_text(s, encoding='utf-8', newline='\n')
    print('Prepared private wrvpn directory mode repair after storage load/restore')
