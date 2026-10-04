#!/usr/bin/env python3
"""Stage monitor ownership checks and bounded stop before service actions."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
script = p.parse_args().source / 'trunk/user/zerotier/zerotier.sh'
text = script.read_text(encoding='utf-8')
functions = r'''monitor_owned() {
	case "$monitor_pid" in ''|*[!0-9]*) return 1 ;; esac
	case "$monitor_birth" in ''|*[!0-9]*) return 1 ;; esac
	current_birth=$(awk '{sub(/^.*\) /, ""); print $20}' "/proc/$monitor_pid/stat" 2>/dev/null)
	[ "$current_birth" = "$monitor_birth" ] || return 1
	# Shell scripts have a shell executable: verify the exact script argument.
	tr '\000' '\n' < "/proc/$monitor_pid/cmdline" 2>/dev/null |
		grep -Fx '/usr/bin/zerotier-monitor.sh' >/dev/null
}
stop_monitor() {
	monitor_record=$(cat /var/run/zerotier-monitor.pid 2>/dev/null)
	[ -n "$monitor_record" ] || return 0
	monitor_pid=${monitor_record%% *}
	monitor_birth=${monitor_record#* }
	if monitor_owned; then
		kill -TERM "$monitor_pid" 2>/dev/null || return 1
		monitor_attempt=0
		while monitor_owned && [ "$monitor_attempt" -lt 6 ]; do
			sleep 1
			monitor_attempt=$((monitor_attempt + 1))
		done
		if monitor_owned; then
			kill -KILL "$monitor_pid" 2>/dev/null || return 1
			sleep 1
			monitor_owned && return 1
		fi
	fi
	# Remove only the same metadata record; never a newer monitor's PID file.
	if [ "$(cat /var/run/zerotier-monitor.pid 2>/dev/null)" = "$monitor_record" ]; then
		rm -f /var/run/zerotier-monitor.pid
	fi
}

'''
anchor = 'start_zero() {\n'
stop_anchor = 'stop_zero() {\n'
if text.count(anchor) != 1 or text.count(stop_anchor) != 1:
    raise SystemExit('Pinned ZeroTier lifecycle anchors mismatch')
text = text.replace(anchor, functions + anchor +
                    '\tstop_monitor || { logger -t zerotier "Monitor did not stop; startup rejected"; return 1; }\n')
text = text.replace(stop_anchor, stop_anchor +
                    '\tstop_monitor || { logger -t zerotier "Monitor did not stop; service stop deferred"; return 1; }\n')
with script.open('w', encoding='utf-8', newline='\n') as out:
    out.write(text)
print('Staged monitor ownership checks and bounded stop')
