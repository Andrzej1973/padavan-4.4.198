# WR1200JS read-only interface snapshot — 2026-10-21

## Follow-up 2026-10-22: owner-run radio-ownership check

The owner ran `powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File
"...\tools\wr1200js-readonly.ps1" -Check radio-ownership` in ordinary Windows
PowerShell and supplied the following complete helper output. Endpoint remains
ASUS@192.168.20.1:22. This is owner-run runtime evidence, not direct executor
access. Earlier quoted-path-only output did not run SSH. Sysfs file timestamps
below are not the time this snapshot was collected.

```text
Read-only router check: radio-ownership (ASUS@192.168.20.1:22)
Allowed command is fixed in this script; no arbitrary remote command input is accepted.
ls: /sys/class/net/ra0/device: No such file or directory
ls: /sys/class/net/ra0/device/driver: No such file or directory
ls: /sys/class/net/ra0/device/driver/module: No such file or directory
lrwxrwxrwx    1 ASUS     root             0 Oct 19 20:54 /sys/class/net/ra0 -> ../../devices/virtual/net/ra0
ls: /sys/class/net/ra1/device: No such file or directory
ls: /sys/class/net/ra1/device/driver: No such file or directory
ls: /sys/class/net/ra1/device/driver/module: No such file or directory
lrwxrwxrwx    1 ASUS     root             0 Oct 19 20:54 /sys/class/net/ra1 -> ../../devices/virtual/net/ra1
ls: /sys/class/net/ra2: No such file or directory
ls: /sys/class/net/ra2/device: No such file or directory
ls: /sys/class/net/ra2/device/driver: No such file or directory
ls: /sys/class/net/ra2/device/driver/module: No such file or directory
ls: /sys/class/net/rai0/device: No such file or directory
ls: /sys/class/net/rai0/device/driver: No such file or directory
ls: /sys/class/net/rai0/device/driver/module: No such file or directory
lrwxrwxrwx    1 ASUS     root             0 Oct 19 20:54 /sys/class/net/rai0 -> ../../devices/virtual/net/rai0
ls: /sys/class/net/rai1/device: No such file or directory
ls: /sys/class/net/rai1/device/driver: No such file or directory
ls: /sys/class/net/rai1/device/driver/module: No such file or directory
lrwxrwxrwx    1 ASUS     root             0 Oct 19 20:54 /sys/class/net/rai1 -> ../../devices/virtual/net/rai1
drwxr-xr-x    5 ASUS     root             0 Oct 18 19:55 /sys/module/mt76x3_ap
drwxr-xr-x    2 ASUS     root             0 Oct 19 22:54 /sys/module/mt76x3_ap/holders
/sys/module/mt76x3_ap/refcnt:1
drwxr-xr-x    5 ASUS     root             0 Oct 18 19:55 /sys/module/mt76x2_ap
drwxr-xr-x    2 ASUS     root             0 Oct 19 22:54 /sys/module/mt76x2_ap/holders
/sys/module/mt76x2_ap/refcnt:1
```

Observations and limits:

- ra0/ra1/rai0/rai1 exist as devices/virtual/net entries, with no device parent
  links at the inspected paths. This lookup cannot establish module ownership;
  absent links do not mean those interfaces have no driver.
- ra2 is absent, corroborating the earlier interface snapshot. This check does
  not inspect br-iot, DHCP or isolation and cannot determine hardware capacity.
- Both module directories exist, both report refcnt 1, and listing their
  holders directories returned no entries. This describes module dependencies
  and references only, not active DMA/interrupts, network clients, RF silence
  or unload/rollback safety.
- No module load/unload, interface-state change, firmware operation or write
  was requested/performed by this fixed check. Do not retry using a destructive
  probe. Continue source ownership/teardown work; radio lifecycle choice is open.

## Follow-up: owner-supplied module snapshot

The owner successfully ran the same fixed helper with `-Check modules` in
ordinary Windows PowerShell and pasted its complete `lsmod` output on
2026-10-21. Endpoint: `ASUS@192.168.20.1:22`. This confirms that the owner's
SSH/helper path works; it does not remove the Codex executor's deny-bin block.
The preceding empty mandatory-parameter error occurred before SSH execution.

```text
Module                  Size  Used by
hw_nat                 67440  0
xt_TPROXY               4016  0
amneziawg             114245  0
zram                   16643  1
ip6table_nat             816  1
nf_nat_ipv6             4531  1 ip6table_nat
xt_HL                   1424  1
iptable_mangle           976  1
fast_classifier        45285  0
shortcut_fe_ipv6       53545  1 fast_classifier
shortcut_fe            52041  1 fast_classifier
nf_nat_ftp              1360  0
nf_conntrack_ftp        5728  1 nf_nat_ftp
ip_set_hash_net        29776  0
ip_set_hash_mac        13328  0
ip_set_hash_ip         25936  0
xt_set                  6096  0
ip_set                 25492  4 ip_set_hash_net,ip_set_hash_mac,ip_set_hash_ip,xt_set
ohci_hcd               23935  0
ehci_hcd               35095  0
usb_storage            40427  0
usblp                   9232  0
mt76x3_ap            1266612  1
mt76x2_ap            1130402  1
```

Both expected Wi-Fi modules are loaded. Their reference counts are not client
counts and do not establish that unloading is safe. In combination with the
board source mapping, this supports targeting mt76x3 for the 2.4 GHz lifecycle
investigation while preserving mt76x2/5 GHz. It does not yet establish device
ownership, holders, reload/rollback safety, or creation of ra2.

Loaded hw_nat, shortcut_fe, fast_classifier, amneziawg and zram establish module
presence only. This output does not prove active flow offload, tunnel traffic,
swap use, Beamforming, or Wi-Fi roaming. No device mutation was performed.

## Provenance and scope

The owner ran the fixed `interfaces` check from
`tools/wr1200js-readonly.ps1` in ordinary Windows PowerShell. The script
reported `ASUS@192.168.20.1:22` and executed its fixed `ifconfig -a` command.
This report summarizes the pasted output; the router was not accessed or
modified by the Codex executor. No settings, services, interfaces or firmware
were changed.

## Relevant observations

| Interface | Snapshot state | Meaning limited to this output |
|---|---|---|
| `br0` | UP/RUNNING, `192.168.20.1/24` | Existing LAN bridge present |
| `ra0` | UP/RUNNING | 2.4 GHz main AP interface present |
| `rai0` | UP/RUNNING | 5 GHz main AP interface present |
| `ra1`, `rai1` | Present, no `UP` flag | These interfaces are down in this snapshot |
| `ra2` | Not listed | No third 2.4 GHz BSS interface is active/listed |
| `br-iot` | Not listed | No separate IoT bridge is active/listed |
| `wg1` | UP/RUNNING, `192.168.30.1/24` | A WireGuard interface is active |
| `eth3` | UP/RUNNING, public WAN address/18 (redacted) | WAN interface is up in this snapshot |

The output includes cumulative counters (`ra0` RX errors 4,388; `rai0` RX
errors 26; `eth3` RX dropped 266,420; `br0` RX dropped 4,735; `wg1` TX errors
156 and dropped 374). These counters alone do not identify cause or indicate
whether errors are currently increasing; no diagnosis is made from them.

## IoT conclusion and limits

This runtime snapshot does not show the expected third AP interface `ra2` or
an isolated `br-iot` bridge. It therefore does not show an active separate IoT
network on the running router. It does not prove whether the Wi-Fi driver or
radio hardware could create `ra2`, nor does it establish DHCP, firewall
isolation, persistence, or a supported production implementation. The source
integration gap remains: IoT must stay OFF and excluded until the authenticated
apply/controller, lifecycle, observation and rollback path is implemented
and verified.
