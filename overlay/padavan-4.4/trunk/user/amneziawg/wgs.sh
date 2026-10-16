#!/bin/sh
umask 077

###

# Empty preserves the existing firmware's automatic choice for saved profiles.
case "$(nvram get vpns_wg_protocol)" in
    wireguard) MODULE="wireguard"; WG="/usr/bin/wg-standard" ;;
    amneziawg) MODULE="amneziawg"; WG="/usr/bin/awg" ;;
    '')
        MODULE="wireguard"
        WG="/usr/bin/wg-standard"
        if [ -d "/lib/modules/$(uname -r)/kernel/net/amneziawg" ]; then
            MODULE="amneziawg"
            WG="/usr/bin/awg"
        fi
        ;;
    *) logger -t vpns 'Invalid tunnel protocol selection'; exit 1 ;;
esac

IF_NAME="wg1"
IF_ADDR="$(nvram get vpns_vnet | sed 's/\.0$/.1/')"
IF_MTU=$(nvram get vpns_wg_mtu)
[ "$IF_MTU" ] || IF_MTU=1420
PORT="$(nvram get vpns_wg_port)"

if [ "$(nvram get vpns_wg_ext_addr)" ]; then
    WAN_ADDR="$(nvram get vpns_wg_ext_addr)"
elif [ "$(nvram get ddns_enable_x)" = "1" ]; then
    WAN_ADDR="$(nvram get ddns_hostname_x)"
else
    WAN_ADDR=$(nvram get wan0_ipaddr)
    [ "$WAN_ADDR" == "0.0.0.0" ] && WAN_ADDR="{wan_address}"
fi

IF_PRIVATE=$(nvram get vpns_wg_private)
if [ ! "$IF_PRIVATE" ]; then
    IF_PRIVATE="$($WG genkey)"
    nvram set vpns_wg_private="$IF_PRIVATE"
    nvram set vpns_wg_public="$(echo $IF_PRIVATE | $WG pubkey)"
    nvram commit
fi

EXPORT_CONF="/tmp/client-wg.conf"
POST_SCRIPT="/etc/storage/vpns_post_script.sh"

###

log()
{
    [ -n "$*" ] || return
    echo "$@"
    logger -t $MODULE "$@"
}

error()
{
    log "$@"
    exit 1
}

die()
{
    echo "$@" >&2
    exit 1
}

is_started()
{
    ip link show ${IF_NAME} >/dev/null 2>&1
    return $?
}

_net_to_prefix()
{
    [ "$1" ] || return

    echo $1 | awk '
    function count1s(N) {
        r=""
        while(N!=0)
        {
            r=((N%2)?"1":"0") r
            N=int(N/2)
        }
        r=gsub(/1/,"",r)
        return r
    }
    function subnetmaskToPrefix(subnetmask)
    {
        split(subnetmask, v, ".")
        return count1s(v[1]) + count1s(v[2]) + count1s(v[3]) + count1s(v[4])
    }
    { print subnetmaskToPrefix($1) }'
}

# Shared by the running server and every exported client configuration.
wg_awg_options()
{
    [ "$MODULE" = "amneziawg" ] || return 0
    local field value jmin jmax s1 s2 h1 h2 h3 h4
    for field in Jc Jmin Jmax S1 S2 H1 H2 H3 H4; do
        case "$field" in
            Jc) value=$(nvram get vpns_awg_jc);;
            Jmin) value=$(nvram get vpns_awg_jmin);;
            Jmax) value=$(nvram get vpns_awg_jmax);;
            S1) value=$(nvram get vpns_awg_s1);;
            S2) value=$(nvram get vpns_awg_s2);;
            H1) value=$(nvram get vpns_awg_h1);;
            H2) value=$(nvram get vpns_awg_h2);;
            H3) value=$(nvram get vpns_awg_h3);;
            H4) value=$(nvram get vpns_awg_h4);;
        esac
        [ -n "$value" ] || continue
        case "$value" in *[!0-9]*) return 1;; esac
        [ "${#value}" -le 10 ] || return 1
        case "$field" in
            Jc) wg_awg_range "$value" 1 128 || return 1;;
            Jmin) wg_awg_range "$value" 0 1279 || return 1; jmin=$value;;
            Jmax) wg_awg_range "$value" 1 1280 || return 1; jmax=$value;;
            S1) wg_awg_range "$value" 0 1132 || return 1; s1=$value;;
            S2) wg_awg_range "$value" 0 1188 || return 1; s2=$value;;
            H1) wg_awg_range "$value" 0 4294967295 || return 1; h1=$value;;
            H2) wg_awg_range "$value" 0 4294967295 || return 1; h2=$value;;
            H3) wg_awg_range "$value" 0 4294967295 || return 1; h3=$value;;
            H4) wg_awg_range "$value" 0 4294967295 || return 1; h4=$value;;
        esac
        printf '%s = %s\n' "$field" "$value"
    done
    if [ -n "$jmin" ] || [ -n "$jmax" ]; then
        [ -n "$jmin" ] && [ -n "$jmax" ] || return 1
        wg_awg_less "$jmin" "$jmax" || return 1
    fi
    if [ -n "$s1" ] && [ -n "$s2" ]; then
        wg_awg_s_pair "$s1" "$s2" || return 1
    fi
    wg_awg_unique "$h1" "$h2" "$h3" "$h4" || return 1
    return 0
}

wg_awg_range()
{
    awk -v n="$1" -v low="$2" -v high="$3" 'BEGIN { if (n !~ /^[0-9]+$/ || n+0 < low || n+0 > high) exit 1 }'
}

wg_awg_less()
{
    awk -v left="$1" -v right="$2" 'BEGIN { if (left+0 >= right+0) exit 1 }'
}

wg_awg_s_pair()
{
    awk -v s1="$1" -v s2="$2" 'BEGIN { if (s1+56 == s2+0) exit 1 }'
}

wg_awg_unique()
{
    awk -v a="$1" -v b="$2" -v c="$3" -v d="$4" \
        'BEGIN { split(a " " b " " c " " d, v, " "); for (i=1; i<=4; i++) if (v[i] != "") for (j=i+1; j<=4; j++) if (v[j] != "" && v[i]+0 == v[j]+0) exit 1 }'
}

wg_setconf()
{
    local pass rnet rmsk prefix i rlan max peers nvram_modified awg_options
    awg_options=$(wg_awg_options) || return 1

    is_started || return 0

    max="$(nvram get vpns_num_x)"
    for i in $(seq 0 $((max-1))); do
        pass=$(nvram get vpns_pass_x$i | $WG pubkey 2>/dev/null)
        [ "$pass" ] || continue
        if [ ! "$(nvram get vpns_public_x$i)" == "$pass" ]; then
            # save public keys to speed up creation of leases
            nvram set vpns_public_x$i="$pass"
            nvram_modified=1
        fi

        rlan=""
        rnet=$(nvram get vpns_rnet_x$i)
        rmsk=$(nvram get vpns_rmsk_x$i)

        if [ "$rnet" -a "$rmsk" ]; then
            prefix=$(_net_to_prefix $rmsk)
            rlan=", $rnet/$prefix"
        fi

        peers=$(echo "[Peer]"
                echo "PublicKey=$pass"
                echo "AllowedIPs=$(nvram get vpns_vnet | sed 's/\.0$/./')$(nvram get vpns_addr_x$i)$rlan"
                echo "$peers")
    done

    [ "$nvram_modified" ] && nvram commit

    cat > "/tmp/${IF_NAME}.conf.$$" <<EOF
[Interface]
ListenPort=${PORT}
PrivateKey=${IF_PRIVATE}
$awg_options
$peers
EOF

    local res status
    res=$("$WG" setconf "$IF_NAME" "/tmp/${IF_NAME}.conf.$$" 2>&1)
    status=$?
    rm -f "/tmp/${IF_NAME}.conf.$$"
    if [ "$status" -eq 0 ]; then
        log "configuration ${IF_NAME} applied successfully, client count: $($WG show ${IF_NAME} peers | wc -l)"
    else
        log "$res"
        return 1
    fi
}

wg_prepare()
{
    modprobe -q $MODULE >/dev/null 2>&1
}

wg_stop()
{
    if is_started; then
        ip link del ${IF_NAME} >/dev/null 2>&1 && log "server stopped"
    fi
}

wg_start()
{
    is_started && die "already started"
    if [ "$MODULE" = "amneziawg" ]; then
        wg_awg_options >/dev/null || error "invalid AmneziaWG server parameters"
    fi
    wg_prepare

    ip link add dev $IF_NAME type $MODULE || error "cannot create $IF_NAME"
    ip link set dev $IF_NAME mtu $IF_MTU
    ip addr add ${IF_ADDR}/24 dev $IF_NAME

    local if_ip=$(ip addr show dev $IF_NAME | awk '/inet/{print $2}')
    [ "$if_ip" ] || error "$IF_NAME interface address not set"

    wg_setconf || die

    if ip link set $IF_NAME up; then
        log "server started, interface: ${IF_NAME}, address: ${IF_ADDR}:${PORT}"
    else
        ip link del $IF_NAME >/dev/null 2>&1
        die "$IF_NAME startup failed"
    fi

    $WG show $IF_NAME allowed-ips | awk '$3 {print $3}' | while read i; do
        ip route add $i dev $IF_NAME metric 1 || log "warning: unable to add route to $i"
    done
}

wg_addclient()
{
    # $1 - client name

    local max nums free_num addr key config awg_options
    awg_options=$(wg_awg_options) || return 1

    max="$(nvram get vpns_num_x)"
    nums=$(for i in $(seq 0 $((max-1))); do
        nvram get vpns_addr_x$i
    done)

    [ ! "$nums" ] && ips=1
    free_num=$(seq 2 255 | grep -vwF "$nums" | head -n1)

    name="client${free_num}_wg"
    [ "$1" ] && name="$1"

    for i in $(seq 0 $((max-1))); do
        [ "$(nvram get vpns_user_x$i)" == "$name" ] && die "already exist"
    done

    addr="$(echo $IF_ADDR | sed 's/\.1$//').$free_num"
    key=$($WG genkey)

    nvram set vpns_user_x$max=$name
    nvram set vpns_pass_x$max=$key
    nvram set vpns_public_x$max=$(echo $key | $WG pubkey)
    nvram set vpns_addr_x$max=$free_num
    nvram set vpns_rnet_x$max=""
    nvram set vpns_rmsk_x$max=""
    nvram set vpns_num_x=$((max+1))
    nvram commit

    wg_setconf || return

    read -r -d '' config <<EOF
[Interface]
PrivateKey = $key
$awg_options
Address = $addr
DNS = 1.1.1.1,8.8.8.8,9.9.9.9,77.88.8.8

[Peer]
PublicKey = $(echo $IF_PRIVATE | $WG pubkey)
Endpoint = ${WAN_ADDR}:${PORT}
PersistentKeepalive = 11
AllowedIPs = 0.0.0.0/0
EOF

    if [ -x /usr/bin/qrencode ]; then
        echo "$config" | qrencode -t UTF8
    fi
    log "client \"$name\" added"
    echo ---------------------------------------------------------
    echo "$config"
    echo
}

wg_listclients()
{
    local peers public_list users_list max

    max="$(nvram get vpns_num_x)"
    [ "$max" == "0" ] && return

    peers=$($WG show ${IF_NAME} dump 2>/dev/null | awk '
        function bf(bytes){
            if (bytes >= 1024^4) printf "%.1fT", bytes/(1024^3)
            else if (bytes >= 1024^3) printf "%.1fG", bytes/(1024^3)
            else if (bytes >= 1024^2) printf "%.1fM", bytes/(1024^2)
            else if (bytes >= 1024) printf "%.1fK", bytes/1024
            else printf "%d", bytes
        } NR>1 {
        print $1, $5, bf($6), bf($7), gensub("[)(]|:[0-9]+$", "", "", $3), $4}
    ')

    if [ ! "$peers" ]; then
        for i in $(seq 0 $((max-1))); do
            rnet=$(nvram get vpns_rnet_x$i)
            rmsk=$(nvram get vpns_rmsk_x$i)

            rlan=""
            if [ "$rnet" -a "$rmsk" ]; then
                prefix=$(_net_to_prefix $rmsk)
                rlan=",$rnet/$prefix"
            fi
            printf "%-12s %s %s%s\n" $(nvram get vpns_user_x$i) $(nvram get vpns_public_x$i) \
                $(nvram get vpns_vnet | sed 's/\.0$/./')$(nvram get vpns_addr_x$i) "$rlan"
        done
        return
    fi

    users_list=$(nvram show all | grep -E "vpns_user_x[0-9]+=.+" \
            | sed -E "s/vpns_user_x([0-9]*)=/vpns_public_x\1|/")
    public_list=$(nvram show all | grep -E "vpns_public_x[0-9]+=.+" \
            | sed -E "s/vpns_public_x([0-9]*)=/vpns_public_x\1|/")

    echo "$peers" | awk -v list1="$users_list" -v list2="$public_list" '
    BEGIN {
        split(list1, parts1, "\n");
        for (i in parts1) {
            split(parts1[i], keyval, "|");
            a[keyval[1]] = keyval[2];
        }

        split(list2, parts2, "\n");
        for (i in parts2) {
            split(parts2[i], keyval, "|");
            b[keyval[1]] = keyval[2]
        }

        for (key in a) {
            if (key in b) {
                c[b[key]] = a[key];
            }
        }
    } { printf "%-12s %s %s ↓%s ↑%s %s %s\n", c[$1], $1, $2, $3, $4, $5, $6, $7}'
}

wg_export()
{
    [ "$1" ] || return

    local i max awg_options
    awg_options=$(wg_awg_options) || return 1

    rm -f "$EXPORT_CONF"

    max="$(nvram get vpns_num_x)"
    for i in $(seq 0 $((max-1))); do
        [ ! "$(nvram get vpns_user_x$i)" == "$1" ] && continue

        tee "$EXPORT_CONF" <<EOF
[Interface]
PrivateKey = $(nvram get vpns_pass_x$i)
$awg_options
Address = $(nvram get vpns_vnet | sed 's/\.0$/./')$(nvram get vpns_addr_x$i)/24
DNS = $(nvram get lan_ipaddr)

[Peer]
PublicKey = $(nvram get vpns_wg_public)
Endpoint = ${WAN_ADDR}:${PORT}
PersistentKeepalive = 11
AllowedIPs = 0.0.0.0/0
EOF
    done

    chmod 0600 "$EXPORT_CONF" || die "not found"
}

case "$1" in
    start)
        wg_start
    ;;

    stop)
        wg_stop
    ;;

    restart)
        wg_stop
        wg_start
    ;;

    export)
        wg_export "$2"
    ;;

    status)
        is_started
    ;;

    add)
        wg_addclient "$2"
    ;;

    list)
        wg_listclients
    ;;

    *)
        echo "Usage: $0 { start|stop|restart|list| { export|add [client name] } }" >&2
        exit 1
    ;;
esac

[ -s "$POST_SCRIPT" -a -x "$POST_SCRIPT" ] && . "$POST_SCRIPT"
