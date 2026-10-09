# Mi Mini profile review — 2026-10-09

Supplied file SHA256: `73222454d22e88f8075a2bc047024e192ec63f0e8e3b8f4e440427bb99ac2442`.

Profile preserves supplied MT7620/MI-MINI board identity, IPv6, USB/filesystems, SSH, AmneziaWG, OpenSSL 3.5, Curl, WPAD and compressed-memory selections. NTFS-3G has FUSE; Dropbear fast code has Dropbear; swap support stays enabled for compressed-memory use. Supplied QUIC had Curl/OpenSSL 3.5 dependencies satisfied, but is commented in the reduced profile. exFAT selects FAT support and EXT4 filesystem tooling is derived by target recipes; separate legacy filesystem flags need not be enabled merely to duplicate those selections.

Commented independent packages: UVC, LPRD, U2EC, HDPARM, EOIP, QUIC and EAP_PEAP. The EAP selector adds PEAP/TTLS/MSCHAPv2 to wpa_supplicant; personal WPA/WPA2 does not require these enterprise methods. Re-enable it if the upstream network actually uses enterprise authentication. Heavy storage/download/media selectors remain documented and disabled. WPAD means proxy auto-discovery/PAC support, not a Wi-Fi roaming daemon.

This is a dependency-reviewed candidate, not a compilable or runtime-verified Mi Mini port. Legacy 3.4 radio selections remain explicitly marked as references; integrated MT7620 2.4 GHz support under the selected 4.4 vendor tree still needs porting. WR1200JS-specific preparation scripts also require board-aware integration before this profile can enter the image matrix. No Mi Mini build or remote changes were performed. AP-client coexistence, Band Steering, RSSI Kick, automatic reconnect and both router/repeater modes require actual driver and device verification.
