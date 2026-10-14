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

No page action starts the daemon, loads a module, binds a device, or changes
persistent configuration. That separation prevents a status refresh from
changing USB ownership.

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
- The new endpoint, page integration, bounded refresh behavior, and EN/UK/RU
  labels have local regression coverage.
- The next full build must prove that the new HTTP endpoint compiles and that
  the page and translations are packaged.
- Module loading, daemon operation, export, connection, data transfer, and
  persistence still require physical-router validation.
