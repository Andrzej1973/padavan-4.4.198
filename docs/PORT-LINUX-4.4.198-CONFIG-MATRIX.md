# WR1200JS Linux 4.4.198: configuration migration status

Updated 2026-10-03. Authoritative development location: Andrzej1973/padavan-4.4.198, main. This replaces the initial symbol audit; its old option counts and preliminary absent-package list are no longer current.

## Configuration preservation

The central policy is [configs.build/wr1200js.config](../configs.build/wr1200js.config). The WR workflow prepares the pinned target and captures firmware-effective.config and kernel-effective.config before compiling isolated diagnostic candidates.

[tools/verify-wr1200js-config.py](../tools/verify-wr1200js-config.py) compares requested firmware selectors against those effective configs. It fails on mismatches, reports disabled missing selectors as not enabled, checks target identity and kernel radio-family selection, and records the CPU_SLEEP request as port_pending. Shortcut FE/SFE and Shadowsocks mode/umbrella mappings are explicit. The report checks configuration, not binary contents, runtime behavior or complete port success. Package/image gates remain separate.

This new gate was added after reference run 37135784110; its real CI execution is not yet proven.

## Build evidence

[Run 37135784110](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37135784110) completed the WR firmware, its enabled image checks, isolated candidates and common download collection. [Exact image evidence](evidence/WR1200JS-BUILD-37135784110.md) records the commit, size and checksums. This evidence applies to that configuration/commit, not arbitrary newly enabled options.

The recipe now includes board-specific partition/DTS files, USB2 support, IMQ/IFB/IPSet, AmneziaWG, OpenSSL 3.5, curl/QUIC, DDNS TLS/logo, WPAD, Stubby, Privoxy, USBIP, Lua, FS tools, TPROXY, EoIP and QR encoding integration paths. Their existing image checks are visible in the workflow; absence from the original upstream template no longer means these ports are absent from prepared sources.

## Explicit unfinished work

- CPU_SLEEP remains requested in the central config but is not implemented in the main image. Only the isolated MT7621 systick kernel candidate has linked. Device integration/runtime validation remain required.
- MT7603E/MT7612E kernel selections are checked; radio EEPROM calibration, actual bands and Wi-Fi/HWNAT stability need device evidence.
- GPIO18 FN1 was added to the DTS in commit 684c2f03245968b0d3fe956751f2a5ee14f5d472. Compilation and physical polarity/action are pending.
- Initial Privoxy editor rendering was corrected in commit b5983f04602ad3b3ba302e536cecf46acf5cc7bb. Compilation, browser save/start and LAN reachability are pending.
- Optional commented NFS, Samba/WINS, SFTP, parted and ADB requests must retain functioning enabled build paths before being called supported. Disabled-default evidence does not verify their enabled configurations.
- Full Wi-Fi roaming capabilities and agreed later runtime-dependent features remain unfinished.

## Current user policy

Performance is preferred; CONFIG_CC_OPTIMIZE_FOR_SIZE is disabled. Do not switch to size optimization or remove existing required features without the agreed space decision.

RPL2TP, DNSCrypt and redsocks2 remain documented optional disabled requests. TOR/GeoIP/GeoIPv6/Zapret/Zapret2 are deferred to stage 2. Storage/server/ADB optional selectors remain commented in the normal profile.

Later user approval superseded the original CAKE exclusion: optional SQM/CAKE is now selected by the central config with router activation disabled by default. Its runtime and acceleration interaction are unverified. Conditional Auto mode remains deferred until its runtime prerequisites pass; it is not an implemented feature.

WR1200JS completion is primary. Mi Mini remains secondary. At the final delivery stage, copy original upstream router configurations unchanged with provenance rather than adapting every other board or enabling unverified matrix targets.

## Device validation and preservation

See [WR1200JS device readiness](WR1200JS-DEVICE-READINESS.md) and [project delivery scope](PROJECT-DELIVERY-SCOPE.md). Current router access is through an AmneziaWG tunnel with no physical recovery operator. No router flash/reboot or Linux 4.4 runtime validation has been performed here.

Own-account source/archive preservation, complete dependency inventory, local backups and rebuild verification remain required; pinned external URLs alone do not complete that work.
