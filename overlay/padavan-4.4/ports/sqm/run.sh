#!/bin/sh
# WR1200JS optional CAKE lifecycle. No persistent acceleration settings changed.
STATE=/var/run/wr1200js-sqm.iface
IFB=sqmifb0
TC=/bin/tc
IP=/bin/ip

valid_iface() {
    case "$1" in ''|*[!A-Za-z0-9_.:-]*) return 1;; esac
    [ "${#1}" -le 15 ] && [ -d "/sys/class/net/$1" ]
}
valid_rate() {
    case "$1" in ''|*[!0-9]*) return 1;; esac
    [ "${#1}" -le 7 ] && [ "$1" -le 2000000 ]
}
owns_qdisc() {
    "$TC" qdisc show dev "$1" 2>/dev/null | grep -q " $2 "
}
stop_sqm() {
    [ -f "$STATE" ] || return 0
    read -r IFACE < "$STATE"
    case "$IFACE" in ''|*[!A-Za-z0-9_.:-]*) return 1;; esac
    [ "${#IFACE}" -le 15 ] || return 1
    if [ -d "/sys/class/net/$IFACE" ]; then
        CURRENT_QDISCS=$("$TC" qdisc show dev "$IFACE") || return 1
        if printf '%s\n' "$CURRENT_QDISCS" | grep -q ' ca01: '; then
            "$TC" qdisc del dev "$IFACE" root || return 1
        fi
        if printf '%s\n' "$CURRENT_QDISCS" | grep -q ' ffff: '; then
            "$TC" qdisc del dev "$IFACE" ingress || return 1
        fi
    fi
    if [ -d "/sys/class/net/$IFB" ]; then
        "$IP" link del dev "$IFB" || return 1
    fi
    rm -f "$STATE"
}

case "$1" in
stop) stop_sqm; exit $?;;
start) ;;
*) exit 1;;
esac
IFACE=$2
valid_iface "$IFACE" || exit 1
UPLINK=$(nvram get sqm_up_speed)
DOWNLINK=$(nvram get sqm_down_speed)
valid_rate "$UPLINK" && valid_rate "$DOWNLINK" || exit 1
[ "$UPLINK" -gt 0 ] || [ "$DOWNLINK" -gt 0 ] || exit 1
[ -x "$TC" ] && [ -x "$IP" ] || exit 1
[ ! -e "$STATE" ] && [ ! -d "/sys/class/net/$IFB" ] || exit 1
"$TC" qdisc show dev "$IFACE" >/dev/null || exit 1
owns_qdisc "$IFACE" ca01: && exit 1
owns_qdisc "$IFACE" ffff: && exit 1
# Record ownership before modifying queues, so a failed start can be cleaned up.
umask 077
printf '%s\n' "$IFACE" > "$STATE" || exit 1
trap 'stop_sqm; exit 1' HUP INT TERM
fail_start() { stop_sqm; exit 1; }
modprobe sch_cake 2>/dev/null || :
if [ "$UPLINK" -gt 0 ]; then
    "$TC" qdisc add dev "$IFACE" root handle ca01: cake \
        bandwidth "${UPLINK}kbit" besteffort nat memlimit 8mb || fail_start
fi
if [ "$DOWNLINK" -gt 0 ]; then
    # Built-in components need no module load; tc/ip provide the real checks.
    modprobe ifb 2>/dev/null || :
    modprobe sch_ingress 2>/dev/null || :
    modprobe cls_u32 2>/dev/null || :
    modprobe act_mirred 2>/dev/null || :
    "$IP" link add "$IFB" type ifb || fail_start
    "$IP" link set dev "$IFB" up || fail_start
    "$TC" qdisc add dev "$IFB" root handle ca02: cake \
        bandwidth "${DOWNLINK}kbit" besteffort nat memlimit 8mb || fail_start
    "$TC" qdisc add dev "$IFACE" handle ffff: ingress || fail_start
    "$TC" filter add dev "$IFACE" parent ffff: protocol all prio 10 u32 \
        match u32 0 0 action mirred egress redirect dev "$IFB" || fail_start
fi
exit 0
