#!/bin/sh
# Candidate policy only: not installed or invoked by production firmware yet.
# Requires serialized lifecycle invocation. Owns only ZTWR_* chains.
# Router access and LAN forwarding are separate explicit settings.

zt_policy_family() {
	zt_ipt="$1"
	zt_family="$2"
	zt_restore="${zt_ipt}-restore"
	command -v "$zt_ipt" >/dev/null 2>&1 || return 1
	command -v "$zt_restore" >/dev/null 2>&1 || return 1
	zt_existing_input=$("$zt_ipt" -S INPUT) || return 1
	zt_existing_forward=$("$zt_ipt" -S FORWARD) || return 1
	zt_input_hooks=$(printf '%s\n' "$zt_existing_input" | awk '$0 == "-A INPUT -j ZTWR_INPUT" {n++} END {print n+0}')
	zt_forward_hooks=$(printf '%s\n' "$zt_existing_forward" | awk '$0 == "-A FORWARD -j ZTWR_FORWARD" {n++} END {print n+0}')
	[ "$zt_input_hooks" -le 32 ] && [ "$zt_forward_hooks" -le 32 ] || return 1
	# Pinned iptables-1.8.7 restore code flushes only explicitly declared
	# custom chains under --noflush. Entire filter update commits atomically.
	{
		printf '*filter\n:ZTWR_INPUT - [0:0]\n:ZTWR_FORWARD - [0:0]\n'
		if [ "$zt_family" = 6 ]; then
			printf '%s\n' '-A ZTWR_INPUT -i zt+ -p ipv6-icmp --icmpv6-type 135 -j ACCEPT'
			printf '%s\n' '-A ZTWR_INPUT -i zt+ -p ipv6-icmp --icmpv6-type 136 -j ACCEPT'
		fi
		if [ "$(nvram get zerotier_router_access)" = 1 ]; then
			printf '%s\n' '-A ZTWR_INPUT -i zt+ -j ACCEPT'
		else
			printf '%s\n' '-A ZTWR_INPUT -i zt+ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT'
		fi
		printf '%s\n' '-A ZTWR_INPUT -i zt+ -j DROP'
		if [ "$(nvram get zerotier_lan_access)" = 1 ]; then
			printf '%s\n' "-A ZTWR_FORWARD -i zt+ -o $zt_lan -j ACCEPT"
			printf '%s\n' "-A ZTWR_FORWARD -i $zt_lan -o zt+ -j ACCEPT"
		fi
		printf '%s\n' '-A ZTWR_FORWARD -i zt+ -j DROP' '-A ZTWR_FORWARD -o zt+ -j DROP'
		while [ "$zt_input_hooks" -gt 0 ]; do
			printf '%s\n' '-D INPUT -j ZTWR_INPUT'
			zt_input_hooks=$((zt_input_hooks - 1))
		done
		while [ "$zt_forward_hooks" -gt 0 ]; do
			printf '%s\n' '-D FORWARD -j ZTWR_FORWARD'
			zt_forward_hooks=$((zt_forward_hooks - 1))
		done
		printf '%s\n' '-I INPUT 1 -j ZTWR_INPUT' '-I FORWARD 1 -j ZTWR_FORWARD' 'COMMIT'
	} | "$zt_restore" --noflush --wait=5
}

zt_policy_nat() {
	zt_existing_nat=$(iptables -t nat -S POSTROUTING) || return 1
	zt_nat_hooks=$(printf '%s\n' "$zt_existing_nat" | awk '$0 == "-A POSTROUTING -j ZTWR_NAT" {n++} END {print n+0}')
	[ "$zt_nat_hooks" -le 32 ] || return 1
	zt_networks=""
	if [ "$(nvram get zerotier_lan_access)" = 1 ] && [ "$(nvram get zerotier_nat)" = 1 ]; then
		# Limit IPv4 masquerading to ZeroTier source prefixes exiting LAN.
		# Refresh after a membership/address change. No overlay-to-WAN NAT.
		zt_addresses=$(ip -o -4 addr show) || return 1
		zt_networks=$(printf '%s\n' "$zt_addresses" | awk '$2 ~ /^zt[a-zA-Z0-9_]+$/ {print $4}' | sort -u)
		for zt_network in $zt_networks; do
			case "$zt_network" in ''|*[!0-9./]*) return 1 ;; esac
			# Kernel restore parser validates actual address/prefix bounds.
		done
	fi
	{
		printf '*nat\n:ZTWR_NAT - [0:0]\n'
		for zt_network in $zt_networks; do
			printf '%s\n' "-A ZTWR_NAT -s $zt_network -o $zt_lan -j MASQUERADE"
		done
		while [ "$zt_nat_hooks" -gt 0 ]; do
			printf '%s\n' '-D POSTROUTING -j ZTWR_NAT'
			zt_nat_hooks=$((zt_nat_hooks - 1))
		done
		printf '%s\n' '-I POSTROUTING 1 -j ZTWR_NAT' 'COMMIT'
	} | iptables-restore --noflush --wait=5
}

zt_policy_apply() {
	zt_lan=$(nvram get lan_ifname)
	[ -n "$zt_lan" ] || zt_lan=br0
	case "$zt_lan" in *[!a-zA-Z0-9_.:-]*|zt*) return 1 ;; esac
	[ -d "/sys/class/net/$zt_lan" ] || return 1
	zt_policy_nat || return 1
	zt_policy_family iptables 4 || return 1
	# A kernel exposing IPv6 must never run an unfiltered overlay family.
	if [ -d /proc/sys/net/ipv6 ] && ! command -v ip6tables >/dev/null 2>&1; then
		return 1
	fi
	if command -v ip6tables >/dev/null 2>&1; then
		zt_policy_family ip6tables 6 || return 1
	fi
}

zt_policy_remove() {
	iptables -t nat -D POSTROUTING -j ZTWR_NAT 2>/dev/null
	iptables -t nat -F ZTWR_NAT 2>/dev/null
	iptables -t nat -X ZTWR_NAT 2>/dev/null
	for zt_ipt in iptables ip6tables; do
		command -v "$zt_ipt" >/dev/null 2>&1 || continue
		for zt_parent in INPUT FORWARD; do
			case "$zt_parent" in INPUT) zt_chain=ZTWR_INPUT ;; FORWARD) zt_chain=ZTWR_FORWARD ;; esac
			# Remove exactly the hook owned by this policy; never flush parent chains.
			"$zt_ipt" -D "$zt_parent" -j "$zt_chain" 2>/dev/null
			"$zt_ipt" -F "$zt_chain" 2>/dev/null
			"$zt_ipt" -X "$zt_chain" 2>/dev/null
		done
	done
	# The daemon is already stopped; absent owned chains are harmless.
	return 0
}
