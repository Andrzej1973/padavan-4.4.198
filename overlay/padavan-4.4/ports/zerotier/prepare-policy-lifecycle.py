#!/usr/bin/env python3
"""Stage scoped policy and background monitoring after prior lifecycle stages."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
directory = root / 'trunk/user/zerotier'
script = directory / 'zerotier.sh'
s = script.read_text(encoding='utf-8')

def replace(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit('Policy lifecycle anchor mismatch: ' + old[:80])
    s = s.replace(old, new)

replace('PLANET="/etc/storage/planet"', 'PLANET="/etc/storage/planet"\numask 077\n. /usr/bin/zerotier-policy.sh || exit 1')
start = s.index('rules() {\n')
end = s.index('zero_route() {\n', start)
s = s[:start] + '''rules() {
	zt_policy_apply
}
del_rules() {
	zt_policy_remove
}

''' + s[end:]
replace('\t# The daemon must not retain the service action lock.',
        '\t# Install scoped rules before any overlay interface can appear.\n'
        '\trules || { logger -t zerotier "Policy installation failed; startup rejected"; return 1; }\n'
        '\t# The daemon must not retain the service action lock.')
replace('\n\trules\n', '\n\t/usr/bin/zerotier-monitor.sh >/dev/null 2>&1 9>&- &\n')
orbit = '''	if [ -n "$moonid" ]; then
		$PROGCLI -D$config_path orbit $moonid $moonid
		logger -t "zerotier" "orbit moonid $moonid ok!"
	fi'''
replace(orbit, '\t# Moon orbit is performed by the bounded background CLI worker.')
replace('\tkill_z\n\tstart_instance', '\tkill_z || return 1\n\tstart_instance')
replace('\tdel_rules\n\tzero_route "del"\n\tkill_z',
        '\tzero_route "del"\n\tkill_z || return 1\n\tdel_rules')
replace('case "$1" in start|stop)', 'case "$1" in start|stop|refresh)')
replace('Usage: zerotier.sh start|stop', 'Usage: zerotier.sh start|stop|refresh')
replace('case $1 in\nstart)', '''case $1 in
refresh)
	[ "$(nvram get zerotier_enable)" = 1 ] || exit 0
	pidof zerotier-one >/dev/null || exit 0
	rules || exit 1
	zero_route "add"
	;;
start)''')
# Preserve configured static routes without waiting for interface assignment.
a = s.index('zero_route() {\n'); b = s.index('monitor_owned() {\n', a)
s = s[:a] + '''zero_route() {
	rulesnum=$(nvram get zero_staticnum_x)
	case "$rulesnum" in ''|*[!0-9]*) return 0 ;; esac
	[ "$rulesnum" -le 64 ] || return 1
	j=0
	while [ "$j" -lt "$rulesnum" ]; do
		route_enable=$(nvram get "zero_enable_x$j")
		zero_ip=$(nvram get "zero_ip_x$j")
		zero_gateway=$(nvram get "zero_route_x$j")
		j=$((j + 1))
		[ "$route_enable" = 1 ] || continue
		case "$zero_ip" in ''|*[!0-9a-fA-F:./]*) continue ;; esac
		case "$zero_gateway" in ''|*[!0-9a-fA-F:.]*) continue ;; esac
		zt0=$(ip route get "$zero_gateway" 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="dev") {print $(i+1); exit}}')
		case "$zt0" in zt*) ;; *) continue ;; esac
		case "$zt0" in *[!a-zA-Z0-9_]*) continue ;; esac
		if [ "$1" = add ]; then
			ip route replace "$zero_ip" via "$zero_gateway" dev "$zt0"
		else
			ip route del "$zero_ip" via "$zero_gateway" dev "$zt0" 2>/dev/null
		fi
	done
	return 0
}

''' + s[b:]
# Abort a restart if the old target daemon remains alive after forced stop.
replace('\t\t\tkill -KILL "$zerotier_process" 2>/dev/null\n',
        '\t\t\tkill -KILL "$zerotier_process" 2>/dev/null\n'
        '\t\t\tsleep 1\n\t\t\tis_zerotier_pid "$zerotier_process" && return 1\n')
replace('\tif [ ! -n "$zmoonid"]; then', '\tif [ -n "$zmoonid" ]; then')
replace('\t\techo "$secret" >$config_path/identity.secret', '\t\techo "$secret" >$config_path/identity.secret\n\t\tchmod 600 "$config_path/identity.secret" || return 1')
with script.open('w', encoding='utf-8', newline='\n') as out:
    out.write(s)
for name, source in (('zerotier-policy.sh', 'firewall-policy.sh'), ('zerotier-monitor.sh', 'zerotier-monitor.sh')):
    shutil.copyfile(Path(__file__).with_name(source), directory / name)
print('Staged scoped policy, background monitor and nonblocking route refresh')
