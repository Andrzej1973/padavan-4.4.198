param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        'identity',
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
        'wifi-show',
        'temperature-paths',
        'txbf-log'
    )]
    [string] $Check
)

$ErrorActionPreference = 'Stop'
$sshExe = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$identityFile = Join-Path $env:USERPROFILE '.ssh\id_ed25519'
$denyBin = Join-Path $env:USERPROFILE '.sbx-denybin'

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
    'wifi-show'       = 'iwpriv rai0 show'
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
