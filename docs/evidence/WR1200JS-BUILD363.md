# WR1200JS build 363 artifact review

Checked 2026-10-17 against GitHub and downloaded artifacts.

- Firmware run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38958637951
- Service run 136: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38958638038
- Both completed successfully at commit 038600db7b2ee210b22e5389eedc97e113729bcb.
- Download artifact: padavan-4.4.198-router-downloads, ID 12072945406.
- Image: WR1200JS_4.4.198.9-363_038600db.trx, 12,562,084 bytes.
- Locally recomputed image SHA256 matches SHA256SUMS and firmware-image-checks.json:
  13065d172b8b15b88a09b19e8647d81a6699d1c261ed62ac7142f35f06ec9bea
- SETUP_WR1200JS.txt identifies this same build and commit and includes 100/300/1000 Mbps guidance.
- Effective kernel config has CONFIG_NET_SCH_CAKE unset. Effective firmware config enables WG/AWG and disables OpenVPN, EoIP and RPL2TP.

Original small CI reports are retained in build363/. The image is not added to Git.
The image report confirms upload structure, lengths and CRCs; it does not prove boot.
The MIPS manager report passes ten cases, including independent WG record creation,
exact exports, rejection handling and preservation of the first record. This resolves
previously pending target fork/exec/store integration, using QEMU/PRoot and image libraries.
The protocol report covers validators and separate native controls; these checks do not
configure live interfaces. The BusyBox report explicitly says whole_service_audit_complete=false
and runtime_verified=false despite passing bounded syntax/applet checks.

Next implementation remains protocol apply/readback, endpoint resolution/pinning,
per-profile address/route/DNS transactions and rollback, then controller/WebUI.
Two simultaneous functioning VPNs, configuration preservation across upgrade, physical
boot, Wi-Fi/WAN behavior and throughput remain unverified. No router changes were made.
