param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        'identity',
        'reboot-capability',
        'diagnostic-inventory',
        'uptime',
        'mtd',
        'pci',
        'pci-config',
        'pci-topology',
        'pci-dump-tools',
        'busybox-version',
        'busybox-image',
        'interfaces',
        'modules',
        'radio-ownership',
        'wifi-commands',
        'wifi-stats',
        'wifi2-stats',
        'wifi2-start-log',
        'wifi2-state',
        'wifi2-bridges',
        'wifi2-build-fingerprint',
        'wifi-show',
        'iot-baseline',
        'temperature-paths',
        'txbf-log'
    )]
    [string] $Check
)

$ErrorActionPreference = 'Stop'
$sshExe = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$identityFile = Join-Path $env:USERPROFILE '.ssh\id_ed25519'
$denyBin = Join-Path $env:USERPROFILE '.sbx-denybin'

# WSL-launched PowerShell can inherit PATHEXT=.CPL and omit OpenSSH from
# PATH. Restore executable discovery for this process before checking the
# resolved command below. Existing deny-bin and alternate-command checks apply.
if (-not (($env:PATHEXT -split ';') -contains '.EXE')) {
    $env:PATHEXT = $env:PATHEXT + ';.EXE'
}
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    $env:PATH = $env:PATH + ';' + (Split-Path -Parent $sshExe)
}

$resolvedSsh = Get-Command ssh -All -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($resolvedSsh -and $resolvedSsh.Source -and
    $resolvedSsh.Source.StartsWith($denyBin, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Codex deny-bin is first in PATH. This helper will not bypass it; run this script from a normal Windows PowerShell session.'
}

if (-not (Test-Path -LiteralPath $sshExe -PathType Leaf)) {
    throw "Windows OpenSSH was not found at the expected system path: $sshExe"
}
if (-not $resolvedSsh -or -not $resolvedSsh.Source -or
    -not [string]::Equals($resolvedSsh.Source, $sshExe, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The normal ssh command does not resolve to Windows OpenSSH. This helper will not select another executable.'
}

if (-not (Test-Path -LiteralPath $identityFile -PathType Leaf)) {
    throw "The configured router identity file is missing: $identityFile. Key contents are never read or displayed."
}

$remoteCommands = @{
    'reboot-capability' = 'busybox zcat /proc/config.gz | grep MAGIC_SYSRQ; ls -l /proc/sysrq-trigger /sbin/reboot; if [ -w /proc/sysrq-trigger ]; then echo sysrq_trigger=writable; fi'
    'diagnostic-inventory' = @'
printf 'KERNEL\n'; uname -r
printf 'FIRMWARE\n'; for key in firmver buildno extendno; do printf '%s=' "$key"; printf '%s\n' "$(nvram get "$key")"; done
printf 'TOOLS\n'
for tool in busybox dmesg logread syslogd klogd ifconfig ip iw iwconfig iwpriv ethtool brctl ss netstat ping traceroute tcpdump iperf3 nslookup dig curl wget wg iptables ip6tables ipset conntrack lsmod modinfo lspci hexdump od sha256sum; do
    found=no
    for dir in /bin /sbin /usr/bin /usr/sbin; do
        if [ -x "$dir/$tool" ]; then found="$dir/$tool"; break; fi
    done
    printf '%s=%s\n' "$tool" "$found"
done
printf 'BUSYBOX_SELECTED_APPLETS\n'
busybox --list | grep -E '^(dmesg|logread|hexdump|od|netstat|ip|nslookup|sha256sum|traceroute)$'
printf 'DATA\n'
for node in /tmp/syslog.log /proc/net/dev /proc/interrupts /proc/meminfo /proc/config.gz /proc/net/nf_conntrack /sys/kernel/debug /sys/class/thermal; do
    if [ -r "$node" ]; then printf '%s=readable\n' "$node"; else printf '%s=unavailable\n' "$node"; fi
done
printf 'KERNEL_LOG\n'; if dmesg >/dev/null 2>&1; then echo dmesg=readable; else echo dmesg=unavailable; fi
printf 'DIAGNOSTIC_MOUNTS\n'; grep -E ' (debugfs|tracefs) ' /proc/mounts
printf 'KERNEL_PRINTK\n'; cat /proc/sys/kernel/printk
printf 'KERNEL_CONFIG\n'
busybox zcat /proc/config.gz | grep -E '^(CONFIG_|# CONFIG_)(IKCONFIG(_PROC)?|DEBUG_FS|DYNAMIC_DEBUG|FTRACE|FUNCTION_TRACER|TRACING|KPROBES|KALLSYMS|KALLSYMS_ALL|PROC_FS|PACKET|NETFILTER_XT_TARGET_TRACE|NF_CONNTRACK_PROCFS|THERMAL)(=| is not set)'
'@
    identity          = 'uname -a'
    uptime            = 'uptime'
    mtd               = 'cat /proc/mtd'
    pci               = 'cat /proc/bus/pci/devices'
    'pci-dump-tools'   = 'command -v busybox 2>/dev/null; busybox --list 2>/dev/null | grep -E "^(od|hexdump|base64|xxd|dd|strings)$"'
    'busybox-version' = 'busybox 2>&1 | head -n 2; command -v busybox 2>/dev/null; ls -l /bin/busybox /usr/bin/busybox 2>&1; busybox --list 2>/dev/null | grep -E "^(od|hexdump|base64|xxd|dd|strings)$"'
    'busybox-image' = 'busybox sha256sum /bin/busybox 2>&1; ls -l /usr/bin/hexdump /usr/bin/od 2>&1; busybox hexdump --help 2>&1 | head -n 25'
    'pci-config'      = @'
for config in /sys/bus/pci/devices/*/config; do
    if [ -r "$config" ]; then
        echo PCI_CONFIG:$config
        busybox hexdump -C -n 4096 "$config"
    else
        echo NO_READABLE_PCI_CONFIG:$config
    fi
done
'@
    'pci-topology'    = @'
for device in /sys/bus/pci/devices/*; do
    echo PCI_DEVICE:$device
    for attribute in vendor device class; do
        if [ -r "$device/$attribute" ]; then
            echo -n "$attribute="
            cat "$device/$attribute"
        fi
    done
    ls -ld "$device" "$device/driver" "$device/subsystem" 2>&1
done
'@
    interfaces        = 'ifconfig -a'
    modules           = 'lsmod'
    'radio-ownership' = @'
for interface in ra0 ra1 ra2 rai0 rai1; do
    ls -ld "/sys/class/net/$interface" "/sys/class/net/$interface/device" "/sys/class/net/$interface/device/driver" "/sys/class/net/$interface/device/driver/module" 2>&1
done
for module in mt76x3_ap mt76x2_ap; do
    ls -ld "/sys/module/$module" "/sys/module/$module/holders" 2>&1
    ls -l "/sys/module/$module/holders/" 2>&1
    grep -H . "/sys/module/$module/refcnt" 2>&1
done
'@
    'wifi-commands'   = 'iwpriv rai0'
    'wifi-stats'      = 'iwpriv rai0 stat'
    'wifi2-stats'     = 'iwpriv ra0 stat'
    'wifi2-start-log' = "grep -aEi 'Band Steering|MT7603|ra2|ra0|RTMP.*(fail|error)|MCU.*(fail|timeout)' /tmp/syslog.log | tail -n 100"
    'wifi2-state'     = 'for key in rt_radio_x mlme_radio_rt rt_guest_enable wr_bs_enable wr_bs_apply_state wr_bs_off_confirmed; do echo $key=$(nvram get $key); done'
    'wifi2-build-fingerprint' = 'busybox sha256sum /sbin/rc /usr/sbin/httpd; for file in /lib/modules/4.4.198/kernel/drivers/net/wireless/mediatek/mt76x3_ap/mt76x3_ap.ko /www/classic-iot-config.js /www/modern/modern-iot.js; do if [ -r "$file" ]; then busybox sha256sum "$file"; fi; done'
    'wifi2-bridges'   = 'for port in /sys/class/net/*/brif/ra0 /sys/class/net/*/brif/ra1 /sys/class/net/*/brif/ra2; do if [ -e "$port" ]; then printf "%s\n" "$port"; fi; done; /usr/sbin/brctl show'
    'wifi-show'       = 'iwpriv rai0 show'
    'iot-baseline' = @'
echo IOT_INTERFACE_COUNTERS
cat /proc/net/dev
for interface in ra0 ra1 ra2; do
    echo IOT_INTERFACE:$interface
    for attribute in ifindex operstate carrier; do
        if [ -r "/sys/class/net/$interface/$attribute" ]; then
            value=$(cat "/sys/class/net/$interface/$attribute" 2>/dev/null)
            if [ $? -eq 0 ]; then
                printf '%s=%s\n' "$attribute" "$value"
            else
                printf '%s=unavailable\n' "$attribute"
            fi
        fi
    done
done
echo IOT_PSM_LOG_TAIL
dmesg | grep -E 'wr_ps event=|mt76x3: ra2 software-off queues-gated' | tail -n 120
'@
    'temperature-paths' = "find /sys/class/thermal /sys/class/hwmon -type f -name '*temp*' 2>/dev/null"
    'txbf-log'        = "dmesg | grep -iE 'txbf|beamform|implicit|explicit|calibrat|eeprom|efuse'"
}

# Preserve POSIX newlines for fixed multiline checks on Windows checkouts.
$remoteCommand = $remoteCommands[$Check].Replace("`r`n", "`n")
$sshArgs = @(
    '-T',
    '-p', '22',
    '-l', 'ASUS',
    '-i', $identityFile,
    '-o', 'BatchMode=yes',
    '-o', 'IdentitiesOnly=yes',
    '-o', 'ConnectTimeout=8',
    '-o', 'ServerAliveInterval=5',
    '-o', 'ServerAliveCountMax=1',
    '-o', 'ClearAllForwardings=yes',
    '-o', 'PermitLocalCommand=no',
    '192.168.20.1',
    $remoteCommand
)

Write-Host "Read-only router check: $Check (ASUS@192.168.20.1:22)"
Write-Host 'Allowed command is fixed in this script; no arbitrary remote command input is accepted.'
& $resolvedSsh.Source @sshArgs
exit $LASTEXITCODE
