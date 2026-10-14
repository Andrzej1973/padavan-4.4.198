# USB/IP integration audit

## Current port boundary

| Component | Current WR1200JS port | Decision |
| --- | --- | --- |
| Kernel source | Pinned Linux 4.4.198 `drivers/usb/usbip` | Keep the kernel implementation unchanged |
| Kernel configuration | `usbip-core`, `usbip-host`, and `vhci-hcd` selected as modules | Build only when `CONFIG_FIRMWARE_INCLUDE_USBIP=y` |
| Userspace | `usbip` and `usbipd` built from the matching Linux 4.4 source | Keep kernel/userspace ABI aligned |
| Runtime dependency | Minimal `libudev.so.1` package | Verify the complete ELF dependency closure |
| Startup | No automatic daemon startup | Keep `usbipd` stopped by default |
| WebUI | Localized, read-only module and process status on the USB/printer page | Add guarded device management only after runtime validation |

## Source and package details

The firmware source is pinned to `vipshmily/padavan-4.4` commit
`c25283e915a2a00a763774dd255b14aff997285e`. The port builds the userspace tools
from that tree's Linux 4.4 USB/IP source and supplies the required minimal
`libudev` package. This avoids mixing the older Linux 3.4 staging ABI with the
4.4.198 kernel.

The image installs:

- `/sbin/usbip`
- `/sbin/usbipd`
- `/lib/libudev.so.1` and its verified dependencies
- `usbip-core.ko`, `usbip-host.ko`, and `vhci-hcd.ko`

The `usbip` command supplies `list`, `bind`, `unbind`, `attach`, `detach`, and
port reporting. `usbipd` serves exported USB devices on TCP port 3240. This
protocol has no built-in client authentication or authorization, so the daemon
must not be exposed to WAN and is not started automatically.

## Kernel support

The WR1200JS overlay requests the following modules:

```text
CONFIG_USBIP_CORE=m
CONFIG_USBIP_VHCI_HCD=m
CONFIG_USBIP_HOST=m
```

The full firmware build checks that all three modules exist in ROMFS, that their
userspace tools are MIPS executables, and that every required shared library is
present. These checks prove image contents, not that the modules can load on a
physical router.

## Runtime status contract

The USB/printer page reports four observations separately:

- core module: `/sys/module/usbip_core`
- export module: `/sys/module/usbip_host`
- client module: `/sys/module/vhci_hcd`
- daemon process: `usbipd`

Each item is rendered as present, absent, or unknown. The page refreshes on
request and every 30 seconds while visible. It does not infer connectivity,
listener reachability, exported-device state, authentication, or successful
data transfer from process presence.

The status integrator requires the requested profile and adds nothing when
`CONFIG_FIRMWARE_INCLUDE_USBIP=y` is absent or commented out. A missing or
unreadable `/sys/module` source yields unknown module states rather than three
claims that modules are unloaded. These refinements follow build 265 and need
their own full-build evidence.

No page action starts the daemon, loads a module, binds a device, or changes
persistent configuration. That separation prevents a status refresh from
changing USB ownership.

## Remaining managed-service implementation

Inspection of pinned `tools/usb/usbip/src/usbipd.c` confirms that PID-file
creation is opt-in: `pid_file` starts as NULL. A controller must pass an explicit
`--pid=/var/run/...` argument; `-D` alone does not establish owned PID state.
The daemon accepts IPv4/IPv6 family selection and a TCP port, but those options
do not restrict it to a LAN interface. Before exposing a start action, integrate
an explicit LAN/VPN access policy with the firewall lifecycle.

SIGTERM/SIGINT interrupt `ppoll`; its error path exits the main loop and removes
the configured PID file. A controller still needs executable/PID ownership
verification, a bounded wait, rejection of an unrelated or untracked process,
and no automatic force-kill fallback. Stopping the parent does not itself prove
that an exported USB device has been unbound or that an existing kernel transfer
has ended; service stop and device export state require separate handling.

Implement device inventory, explicit export/unexport, validated persistent
configuration and authenticated actions together with failure recovery. These
remain required work; the current observation panel does not fulfill them.

`tools/usbip/firewall-policy.sh` is an uninstalled component for the managed
IPv4 daemon. It owns `WRUSBIP_INPUT`, installs a first INPUT hook atomically
through `iptables-restore --noflush`, accepts TCP 3240 on loopback and the
validated LAN interface, and drops that port on other interfaces. Other traffic
returns to the original policy. It must be applied before `usbipd -4` starts
and removed only after confirmed stop; retaining an empty owned chain avoids
deleting references from other tools. VPN access is not implicitly granted.
The isolated test executes the shell functions with mocked command results;
real netfilter behavior, firewall rebuild integration and lifecycle sequencing
still require verification before packaging.

`tools/usbip/service.sh` now provides an uninstalled start/stop/restart/status
candidate. It serializes actions with flock, checks the explicit PID file and
executable, rejects untracked processes, applies the LAN policy before module
loading and daemon startup, and invokes IPv4-only `usbipd -4 -D --pid=...`.
Stop waits up to ten polling intervals after SIGTERM; failure retains the
restrictive policy and aborts restart. The script does not bind/unbind devices,
write NVRAM, force-kill workers, or infer transfer success from a running PID.
Its isolated fixture replaces process paths and signal delivery; tests cannot
establish real process races, USB behavior or netfilter behavior. Packaging,
boot/persistent configuration, firewall rebuild ordering and authenticated UI
actions remain open.

## Manual commands and risk boundary

The relevant commands for later physical validation are:

```sh
lsmod | grep -E 'usbip|vhci'
usbip list -l
usbip list -r <server>
usbip bind -b <busid>
usbip unbind -b <busid>
usbip attach -r <server> -b <busid>
usbip detach -p <port>
usbipd -D
```

`bind`, `unbind`, `attach`, and `detach` change kernel device association or
remote attachment. They are documentation for a supervised validation window;
they have not been run on the user's router. A complete transfer test also
requires a second USB/IP-capable host.

## Validation status

- Build 263 proved the USB/IP tools, modules, and ELF dependency closure in the
  complete WR1200JS image.
- Source transformation and EN/UK/RU label insertion have local regression
  coverage. A Node fixture executes the emitted renderer and refresh functions:
  mixed module/process states, malformed replies, failure clearing, hidden-page
  suppression, one outstanding request and recovery pass. It mocks AJAX and DOM;
  it does not execute C, a real browser, or the router HTTP server.
- [Service run 38607744181](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38607744181)
  executed the extracted C endpoint with native address/undefined-behavior
  sanitizers and mocked sysfs/proc observations. Source failures, module absence,
  process states and invalid arguments passed. This is not physical sysfs or
  process-enumeration validation.
- [Build 265](evidence/WR1200JS-BUILD265.md) proves compilation of the new HTTP
  endpoint and packaging of the page and dictionary title keys. Full rendering
  and refresh behavior remain unverified on a device.
- Module loading, daemon operation, export, connection, data transfer, and
  persistence still require physical-router validation.
