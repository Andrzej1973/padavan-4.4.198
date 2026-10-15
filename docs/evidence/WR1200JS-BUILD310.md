# WR1200JS test build 310 — WAN switch topology evidence

[Full run 38794007416](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38794007416)
and [service CI 38794007264](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38794007264)
succeeded at `5e3c62ef204206f878cf79164fb6fb76ac1bbed5`. The newer service CI
[38794541983](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38794541983)
succeeded at HEAD `c38ec51f00b58b9831f54f3aef8bf83fad16af20`, so the VLAN-table
transformation fixture has now executed and passed.

Artifact `WR1200JS_4.4.198.9-310_5e3c62ef_TEST` (ID 12002072335) was downloaded
into `../build310-evidence/zip`. Independent SHA256 and sizes:

- `WR1200JS_4.4.198.9-310_5e3c62ef.trx`: 12,620,743 bytes;
  `e9600df85001e3d02cace635036f10218cafaafb4fbbdaaa93a0b4b658925499`.
- `SETUP_WR1200JS.txt`: 36,694 bytes;
  `78dde760b393caba4f77fdbea88c1a28e3ad8bb3e1ae4e49347e5b43ce555676`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The configuration is byte-identical to `configs.build/wr1200js.config`, so the
requested configuration is preserved in the packaged image. The guide names
build 310, the version tag `310_5e3c62ef` and the full commit, and passes
`tools/check-router-guide.py`. The image passes the project verifier
`overlay/padavan-4.4/scripts/verify-wr1200js-image.py` with all six checks true:
uImage magic, ProductID `WR1200JS`, header CRC, declared length, payload CRC and
size range. That verifier states its own limit — device boot unverified.

## WAN switch topology evidence

`wan-port-topology.json` (artifact ID 12001613150) is preserved here as
`WR1200JS-BUILD310-TOPOLOGY.json`. It resolves, from the exact driver headers and
the effective kernel config of this build:

- Original WAN = external port 0, LAN = external ports 1–4.
- CPU WAN = port 5, CPU LAN = port 6, i.e. the header branch selected by
  `CONFIG_MT7530_GSW`, `CONFIG_GE2_INTERNAL_GMAC_P5` and
  `CONFIG_RAETH_BOTH_GMAC` is the effective one, even though those macros are
  absent from the Kconfig file.
- Masks: WAN `1`, LAN `30`, CPU WAN `32`, CPU LAN `64`, excluded `0`.
- Five plans: selection 0 restores the original WAN; selections 1–4 move the
  external WAN role to LAN1–LAN4 and isolate the damaged original WAN
  (`isolated_external = 1`).

Independent reconciliation of that report: the sha256 of the build's
`kernel-effective.config` is
`aa031a8b53f067b3b899279b103acb596384bf48713873da0f2c63645507cf8e`, identical to
the value recorded inside the JSON, and that config carries
`CONFIG_RAETH_ESW_PORT_WAN=0` together with `CONFIG_RAETH_ESW_PORT_LAN1..4=1..4`.

Not verified from this report: the recorded sha256 of `ioctl_mt762x.h` and
`esw_common.h` could not be re-derived, because neither header is uploaded as an
artifact and neither exists in the working copy (only `sources/*.lock.json`
references them). The report keeps `source_only=true` and
`runtime_verified=false`, and the same limits remain here.

## Unchanged evidence carried over from build 309

The EoIP and web-route artifacts are byte-identical to build 309:
`EOIP-BUILD310-IMAGE.json` sha256
`311f03d90b40cef9618301028046789bed802ddc96ff284c6d79913875fd6974` and
`WR1200JS-BUILD310-ROUTES.json` sha256
`4fdfcb8dd25026a12af2c636080edfcf4328b0ec722ea57cfbd7e70af64a431e`. No EoIP or
route regression was introduced between the two builds; the new content of build
310 is the topology report.

`zram-image-checks.txt` records `PASS zram dependencies, rc command and image
BusyBox priority/discard help under QEMU; activation unverified`. CAKE remains
excluded: the packaged configuration carries `CONFIG_FIRMWARE_INCLUDE_SQM=n`.

## Open

A full build on HEAD `c38ec51`, which carries the VLAN-table transformation
candidate, is still absent; only the fast service job has run on it, and that
job did execute both new fixtures:
`PASS WAN external-port plan: original/each LAN, old-WAN isolation, reversed
mapping and invalid maps` and `PASS WAN VLAN plan: CPU/remaining-LAN
preservation, tagged rules, PVID and IPTV conflicts`, compiled with
`-Wall -Wextra -Werror` and ASan/UBSan.

The device was not reachable from the sandbox (TCP 22 on `192.168.20.1` closed),
and no flashing, reboot, settings mutation or tunnel creation was performed.
Physical acceptance of EoIP, of WAN reassignment and of the whole Linux 4.4.198
port remains open, as does the driver runtime ABI for WAN/LAN masks, VLAN
membership and PVIDs.
