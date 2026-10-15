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
through `iptables-restore --noflush`, returns TCP 3240 on loopback and the
validated LAN interface to the existing policy, and drops that port on other interfaces. Other traffic
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

Firewall rebuild integration now uses `tools/usbip/prepare-firewall.py` when
USB/IP is selected. All four stock IPv4/IPv6 normal/default filter generators
declare `WRUSBIP_BASE` and emit its INPUT hook before established-connection
acceptance. LAN and loopback return to the stock rules, preserving MAC policy;
other interfaces drop TCP 3240 even when the global firewall is disabled.
Invalid LAN names fail closed for non-loopback traffic. The chain and hook are
committed with the complete filter table, avoiding a post-restore exposure gap.
Local transformation of the actual baseline passed; native emitter CI and the
next complete firmware build must pass before claiming compilation/packaging.
Persistent enable settings, boot actions and managed UI are still absent.

Build 274 at `8d634d7a2dd83dcb62e69c80e18999556dd744a4` completed successfully:
[full build](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38639823148).
The [service checks](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38639823051)
also passed. This proves compilation of the firewall integration, not physical
netfilter behavior or a USB transfer. The final artifact has not been downloaded
or hashed in this step.

The next increment packages the existing controller as `/usr/sbin/wr-usbip`
and its policy as `/usr/libexec/wr-usbip/firewall-policy.sh`. Image gates compare
both installed files byte for byte with their sources and check the executable
controller. No boot hook or persistent enable setting is added in this increment;
the daemon does not start automatically. Packaging awaits its own complete build.
For supervised manual operation use `wr-usbip start|stop|restart|status` rather
than invoking the daemon directly. Status exit zero means an owned daemon was
observed, not successful USB data transfer. USB export remains a separate action.

`tools/usbip/prepare-lifecycle.py` now adds `APP_USBIP` only for the selected
package, an NVRAM default `usbip_enable=0`, and boot/shutdown calls in RC.
Boot starts the owned controller only for the exact value `1`; startup failure
is logged without aborting the remaining service sequence. Shutdown attempts
the managed stop and logs an unconfirmed stop. No existing NVRAM value is
overwritten by this generator. Its changes were applied successfully to the
actual baseline locally; compilation and device persistence remain unverified.
No UI action or automatic USB export is supplied by these hooks. A saved
enable value alone does not prove that a daemon or USB transfer is working.

The next web increment (`tools/usbip/prepare-web.py`) registers `usbip_enable`
in General Apply with a dedicated event bit 55 (rejecting an occupied bit),
the RC notification `restart_usbip`, and a 25-second Apply estimate. It uses
the existing authenticated Apply path; no new command endpoint is introduced.
Exact value `1` requests the managed restart, other values request stop.
Restart preserves the controller's stop-failure gate. EN/UK/RU help explicitly
separates the requested setting from observed process/module status and warns
that export is manual and the USB/IP protocol has no user authentication.
The transformation passed locally against baseline C/ASP with fixture
dictionaries; Python compilation passed. Full compilation, browser Apply,
authentication behavior, data transfer and reboot persistence remain unverified.

Correction after full run 38740589879: preparation rejected bit 55 because the
ZRAM patch already reserves it; Stubby uses the last remaining bit 56. No
firmware was produced by that run. USB/IP now uses `EVM_RESTART_SPOOLER`, the
existing USB-service Apply transaction, with a 25-second wait estimate. Its RC
handler calls `wr-usbip reconcile`: enabled and already owned means no restart;
enabled and stopped starts; disabled stops. Ownership failures remain errors.
The existing printer-spooler refresh also runs for a USB/IP setting change;
this is an explicit shared-event dependency, not an independent USB/IP event.
No ZRAM, Stubby or ZeroTier event is changed. A source fixture covers a disabled
profile, preservation of an occupied bit, labels, event wiring, and duplicate
rejection. The Linux lifecycle fixture additionally checks reconciliation and
stop timeout. These checks do not establish physical USB behavior.

[CI 38639330507](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38639330507)
passed at `33c5d91a0a67047256274f2809d391920a5d34a0`: shell syntax,
isolated lifecycle/policy checks and the existing service checks. The daemon
launch closes lock descriptor 9; the fixture rejects inherited descriptor 9.
This prevents the daemon from keeping the controller lock after startup.
The tests mock daemon, signals, module loading and policy application; no live
router lifecycle action was performed.

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
