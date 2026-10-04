#!/bin/sh
# Staged monitor only: not installed or started by production firmware yet.
# Run as a standalone process; lifecycle caller must close its action-lock fd.
umask 077
PROG=/usr/bin/zerotier-one
PROGCLI=/usr/bin/zerotier-cli
HOME_PATH=/etc/storage/zerotier-one
RUN_PATH=/var/run
PID_FILE="$RUN_PATH/zerotier-monitor.pid"
CLI_PID=""
CLI_BIRTH=""
CLI_GATE=""
CLI_SEQUENCE=0
CLI_STALLED=0

process_birth() {
	case "$1" in ''|*[!0-9]*) return 1 ;; esac
	awk '{sub(/^.*\) /, ""); print $20}' "/proc/$1/stat" 2>/dev/null
}
stop_owned_cli() {
	[ -n "$CLI_PID" ] && [ -n "$CLI_BIRTH" ] || return 0
	if [ "$(process_birth "$CLI_PID")" = "$CLI_BIRTH" ]; then
		kill -TERM "$CLI_PID" 2>/dev/null
		sleep 1
		if [ "$(process_birth "$CLI_PID")" = "$CLI_BIRTH" ]; then
			kill -KILL "$CLI_PID" 2>/dev/null
		fi
	fi
}
cleanup() {
	[ -z "$CLI_GATE" ] || rm -f "$CLI_GATE"
	stop_owned_cli
	if [ "$(cat "$PID_FILE" 2>/dev/null)" = "$$ $MONITOR_BIRTH" ]; then
		rm -f "$PID_FILE"
	fi
	rm -f "$RUN_PATH/zerotier-info.tmp" "$RUN_PATH/zerotier-networks.tmp" "$RUN_PATH/zerotier-state.tmp" "$RUN_PATH/zerotier-orbit.tmp"
}
daemon_running() {
	for daemon_pid in $(pidof zerotier-one); do
		if [ "$(readlink "/proc/$daemon_pid/exe" 2>/dev/null)" = "$PROG" ]; then return 0; fi
	done
	return 1
}
cli_capture() {
	cli_command="$1"
	cli_output="$2"
	shift 2
	# Hold the child until its /proc identity is recorded. If recording fails,
	# it exits without executing CLI after at most three seconds.
	CLI_SEQUENCE=$((CLI_SEQUENCE + 1))
	CLI_GATE="$RUN_PATH/zerotier-cli-gate.$$.$CLI_SEQUENCE"
	rm -f "$CLI_GATE"
	(
		exec 8>&-
		gate_attempt=0
		while [ ! -f "$CLI_GATE" ] && [ "$gate_attempt" -lt 3 ]; do
			sleep 1
			gate_attempt=$((gate_attempt + 1))
		done
		[ -f "$CLI_GATE" ] || exit 125
		exec "$PROGCLI" "-D$HOME_PATH" "$cli_command" "$@" > "$cli_output" 2>/dev/null
	) &
	CLI_PID=$!
	CLI_BIRTH=$(process_birth "$CLI_PID")
	if [ -z "$CLI_BIRTH" ]; then
		# Never wait on an unidentified child; the unopened gate expires itself.
		CLI_PID=""
		CLI_GATE=""
		CLI_STALLED=1
		return 125
	fi
	if ! : > "$CLI_GATE"; then
		stop_owned_cli
		CLI_STALLED=1
		return 125
	fi
	attempt=0
	while [ "$(process_birth "$CLI_PID")" = "$CLI_BIRTH" ] && [ "$attempt" -lt 4 ]; do
		sleep 1
		attempt=$((attempt + 1))
	done
	if [ "$(process_birth "$CLI_PID")" = "$CLI_BIRTH" ]; then
		stop_owned_cli
		# SIGKILL cannot release a task in uninterruptible kernel sleep.
		# Do not call wait on the timeout path.
		CLI_STALLED=1
		cli_result=124
	else
		wait "$CLI_PID"
		cli_result=$?
	fi
	rm -f "$CLI_GATE"
	CLI_GATE=""
	CLI_PID=""
	CLI_BIRTH=""
	return "$cli_result"
}

mkdir -p "$RUN_PATH" || exit 1
exec 8> "$RUN_PATH/zerotier-monitor.lock" || exit 1
flock -n 8 || exit 0
MONITOR_BIRTH=$(process_birth "$$")
[ -n "$MONITOR_BIRTH" ] || exit 1
printf '%s\n' "$$ $MONITOR_BIRTH" > "$PID_FILE" || exit 1
trap 'cleanup' EXIT
trap 'exit 0' TERM INT

# Background startup has a deadline; controller authorization is not awaited.
startup_attempt=0
while ! daemon_running && [ "$startup_attempt" -lt 10 ]; do
    sleep 1
    startup_attempt=$((startup_attempt + 1))
done
daemon_running || exit 1
moon_id=$(nvram get zerotier_moonid)
case "$moon_id" in *[!0-9a-fA-F]*) moon_id="" ;; esac
[ "${#moon_id}" -le 16 ] || moon_id=""
moon_attempt=0
while [ "$CLI_STALLED" -eq 0 ] && [ "$(nvram get zerotier_enable)" = 1 ] && daemon_running; do
    if [ -n "$moon_id" ] && [ "$moon_attempt" -lt 12 ]; then
        moon_attempt=$((moon_attempt + 1))
        if cli_capture orbit "$RUN_PATH/zerotier-orbit.tmp" "$moon_id" "$moon_id"; then
            moon_id=""
        fi
        rm -f "$RUN_PATH/zerotier-orbit.tmp"
    fi
    # Refresh addresses/routes and restore owned hooks after ordinary changes.
    # A synchronous firewall-restart hook is still required before production.
    if ! /usr/bin/zerotier.sh refresh 8>&-; then
        logger -t zerotier "Overlay policy refresh failed"
    fi
	# No wait for interface creation or controller authorization.
	if cli_capture info "$RUN_PATH/zerotier-info.tmp"; then
		mv -f "$RUN_PATH/zerotier-info.tmp" "$RUN_PATH/zerotier-info.txt"
	else
		printf '%s\n' 'Node status temporarily unavailable' > "$RUN_PATH/zerotier-info.txt"
	fi
	if [ "$CLI_STALLED" -eq 0 ] && cli_capture listnetworks "$RUN_PATH/zerotier-networks.tmp"; then
		mv -f "$RUN_PATH/zerotier-networks.tmp" "$RUN_PATH/zerotier-networks.txt"
	else
		printf '%s\n' 'Network status temporarily unavailable' > "$RUN_PATH/zerotier-networks.txt"
	fi
	{
		printf 'Updated at Unix time %s\n' "$(date +%s)"
		cat "$RUN_PATH/zerotier-info.txt" "$RUN_PATH/zerotier-networks.txt"
	} > "$RUN_PATH/zerotier-state.tmp" &&
		mv -f "$RUN_PATH/zerotier-state.tmp" "$RUN_PATH/zerotier-state.txt"
	# Stop polling after a stuck/unidentified child; do not accumulate workers.
	[ "$CLI_STALLED" -eq 0 ] || break
	sleep 10
done
