# USB/IP integration audit

## Comparison result

| Function | Hadzhioglu `master` | nilabsent WR1200JS base | Action |
| --- | --- | --- | --- |
| USB/IP kernel source | Present under `drivers/staging/usbip` | Present | Keep nilabsent kernel source; copy none |
| USB/IP kernel configuration | Enabled where selected by board configuration | Source exists, but WR1200JS had `CONFIG_EXPERIMENTAL` disabled and no USB/IP module selections | Enable only the prerequisite and three USB/IP modules for WR1200JS |
| USB/IP userspace | `trunk/user/usbip` | Missing | Import upstream package sources |
| `libsysfs` dependency | `trunk/user/sysfsutils` | Missing | Import and build before USB/IP |
| Build hooks | `sysfsutils` and `usbip` under USB support, gated by `CONFIG_FIRMWARE_INCLUDE_USBIP` | Missing | Patch the existing USB support block |
| Startup / WebUI | No USB/IP service or WebUI integration found in the package or rc references | None | Keep daemon manual; add no page or startup policy |

## Upstream source and package details

The source is pinned to Hadzhioglu `master` commit `503a6f0064bc5999bf92e47a902a732693a1a4f5` (2026-09-06). The build imports only `trunk/user/usbip` and `trunk/user/sysfsutils`; it verifies the checked-out commit before copying those directories. This makes future upstream changes explicit rather than silently changing the firmware build.

`sysfsutils/Makefile` builds `libsysfs.so` from its listed library objects and installs it as `/lib/libsysfs.so`, with compatibility symlinks `.so.2` and `.so.2.1.0`.

`usbip/Makefile` builds `libusbip.so` and the two programs. The library is built from `names.c`, `usbip_host_driver.c`, `usbip_common.c`, and `vhci_driver.c`; it links against `libsysfs`. The programs also link against `libsysfs` and `libusbip`. Upstream installs:

- `/sbin/usbip`
- `/sbin/usbipd`
- `/lib/libusbip.so` and compatibility symlinks
- `/lib/libsysfs.so` and compatibility symlinks

The earlier status note listed `/usr/bin/usbip`; that path was incorrect. Upstream installs both programs in `/sbin`.

The build is direct Makefile logic with no autotools/configure step. `usbip` includes `list`, `bind`, `unbind`, `attach`, `detach`, and port reporting commands. `usbipd` serves exported USB devices over TCP port 3240. Upstream documentation states the daemon has no client authentication or authorization.

## Kernel support

The nilabsent kernel already contains `usbip-core`, `vhci-hcd`, and `usbip-host` sources in `trunk/linux-3.4.x/drivers/staging/usbip`. The WR1200JS kernel config already enables `CONFIG_USB=y`, `CONFIG_NET=y`, `CONFIG_SYSFS=y`, and modules. It did not select USB/IP, and the base Kconfig makes `USBIP_CORE` depend on `EXPERIMENTAL`.

The overlay therefore enables `CONFIG_EXPERIMENTAL=y` and builds these existing nilabsent drivers as modules:

```text
CONFIG_USBIP_CORE=m
CONFIG_USBIP_VHCI_HCD=m
CONFIG_USBIP_HOST=m
```

This supplies `usbip-core.ko`, `vhci-hcd.ko`, and `usbip-host.ko` without copying or modifying kernel source. The board build must confirm these modules are included in the firmware image.

## Runtime and service behavior

No Hadzhioglu USB/IP rc startup hook or WebUI was found. The package only installs the daemon; it does not start it. Use `usbipd -D` on a device sharing USB peripherals, after loading `usbip-host`. Use `usbip attach` on a client after loading `vhci-hcd`. `usbip bind` and `usbip unbind` control the server-side device driver association.

The relevant checks on a built router are:

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

`bind`, `unbind`, `attach`, and `detach` change kernel device associations or remote device attachments. These commands are documented for post-build validation only; they were not run against a real router. A remote-access test also requires a second USB/IP-capable host.

## Validation status

- Source trees, Makefiles, install paths, kernel Kconfig dependencies, and WR1200JS kernel settings were inspected.
- Both new patches passed an apply check against the inspected nilabsent source contexts.
- Cross-compilation, firmware contents, module loading, and network runtime behavior still require a full WR1200JS build and device or emulator validation.
