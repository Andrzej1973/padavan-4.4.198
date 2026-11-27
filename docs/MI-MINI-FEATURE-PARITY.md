# Mi Mini R1CM feature parity

Baseline is the supplied Mi Mini profile. This inventory compares explicit enabled source selectors. Implicit stock features still need recipe and image evidence.

| Selector | Reference | Candidate |
| --- | --- | --- |
| `CONFIG_FIRMWARE_CPU_600MHZ` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_EXFAT` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_EXT4` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_FUSE` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_IPV6` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_SWAP` | Enabled | Enabled |
| `CONFIG_FIRMWARE_ENABLE_USB` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG` | — | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_CURL` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_DDNS_SSL` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_DNSCRYPT` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_DOH` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_DROPBEAR` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_DROPBEAR_FAST_CODE` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_EAP_PEAP` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_EOIP` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_FTPD` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_FTPD_SSL` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_HDPARM` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_HTTPS` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_IPSET` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_LANG_RU` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_LANG_UK` | — | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_LPRD` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_LUA` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_MINIDLNA` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_NTFS_3G` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_OPENSSL_35` | — | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_OPENSSL_EC` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_QUIC` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_SFTP` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_SHORTCUT_FE` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_SMBD` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_STUBBY` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_TRANSMISSION` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_TRANSMISSION_WEB_CONTROL` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_U2EC` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_UVC` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_WPAD` | Enabled | Enabled |
| `CONFIG_FIRMWARE_INCLUDE_XUPNPD` | Enabled | — |
| `CONFIG_FIRMWARE_INCLUDE_ZRAM` | Enabled | Enabled |

## Target evidence

- Both radio drivers and APCLI compiled with MT7612E modular. The staged module resolves PCI alias 14c3:7612. [Module CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46041332550) Cross-band forwarding and reconnect are NOT RUN.
- The diagnostic kernel includes usblp. [USB driver CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46032959355) The final image, RAW printing, LPR printing, concurrent USB jobs and LAN-only access are NOT RUN.
- An absent candidate selector requires a compatibility and size decision. See [dependency review](MI-MINI-DEPENDENCY-REVIEW.md) and [port status](mi-mini-port-status.md).
