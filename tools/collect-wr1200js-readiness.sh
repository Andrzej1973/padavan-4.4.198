#!/bin/sh
# Read-only diagnostic collection: output goes to stdout for saving on the PC.
# No NVRAM dump, flash writes, reboot, service restart, or settings changes.
section()
{
    printf '\n## %s\n' "$1"
}
section 'Collection time and kernel'
date -u
uname -a
cat /proc/uptime
section 'Flash partition map'
cat /proc/mtd
section 'CPU and memory'
cat /proc/cpuinfo
cat /proc/meminfo
section 'Mounted filesystems and temporary space'
cat /proc/mounts
df -h /tmp
section 'Network interface state and counters'
ip -s link show
section 'IPv4 addresses and routes'
ip -4 address show
ip -4 route show
section 'Policy routing and additional IPv4 tables'
ip -4 rule show
ip -4 route show table all
section 'IPv6 addresses and policy routing'
ip -6 address show
ip -6 rule show
ip -6 route show table all
section 'Tunnel tool paths and interface names only'
for tool in wg awg; do
    if command -v "$tool" >/dev/null 2>&1; then
        command -v "$tool"
        "$tool" show interfaces 2>&1
    fi
done
# Do not use showconf, dump, or an NVRAM export here: those can expose keys.
section 'Wireless interfaces'
if command -v iwconfig >/dev/null 2>&1; then iwconfig 2>&1; fi
section 'Loaded kernel modules'
cat /proc/modules
section 'Interrupt and softirq counters'
cat /proc/interrupts
if [ -r /proc/softirqs ]; then cat /proc/softirqs; fi
section 'CPU topology and slab allocation snapshot'
for path in /sys/devices/system/cpu/online /sys/devices/system/cpu/possible /proc/slabinfo; do
    if [ -r "$path" ]; then
        printf '\n%s\n' "$path"
        cat "$path"
    fi
done
section 'Selected service process IDs only'
for service in httpd dnsmasq vlmcsd inadyn stubby privoxy; do
    printf '%s: ' "$service"
    pidof "$service" 2>/dev/null || printf 'not running\n'
done
section 'WPAD endpoint file links'
for name in wpad.dat wpad.da proxy.pac; do
    ls -ld "/www/$name" 2>/dev/null || :
done
section 'Device-tree identity and button nodes'
dt=/sys/firmware/devicetree/base
for name in model compatible; do
    if [ -r "$dt/$name" ]; then
        printf '%s: ' "$name"
        tr '\000' '\n' < "$dt/$name"
    fi
done
for name in reset wps fn1 fn2; do
    node="$dt/gpio-keys-polled/$name"
    if [ -d "$node" ]; then
        printf '%s: present\n' "$name"
        if command -v od >/dev/null 2>&1; then
            for property in gpios linux,code; do
                if [ -r "$node/$property" ]; then
                    printf '%s (raw bytes, device-tree big endian): ' "$property"
                    od -An -tx1 "$node/$property"
                fi
            done
        fi
    else
        printf '%s: no device-tree node\n' "$name"
    fi
done
section 'LED names, brightness and selected triggers'
for led in /sys/class/leds/*; do
    [ -d "$led" ] || continue
    printf '\n%s\n' "$led"
    for property in brightness max_brightness trigger; do
        if [ -r "$led/$property" ]; then
            printf '%s: ' "$property"
            cat "$led/$property"
        fi
    done
done
if [ -r /sys/kernel/debug/gpio ]; then
    section 'Existing GPIO debug ownership snapshot'
    cat /sys/kernel/debug/gpio
fi
section 'Boot and driver kernel log'
dmesg
section 'End of collection'
