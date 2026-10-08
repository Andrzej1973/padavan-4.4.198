# Padavan 4.4.198

Padavan firmware for **YOUHUA WR1200JS**, based on [vipshmily/padavan-4.4](https://github.com/vipshmily/padavan-4.4/tree/c25283e915a2a00a763774dd255b14aff997285e), with selected components from [nilabsent/padavan-ng](https://github.com/nilabsent/padavan-ng). Original project: [Padavan / rt-n56u](https://bitbucket.org/padavan/rt-n56u).

## Selected packages and features

The [WR1200JS configuration](configs.build/wr1200js.config) enables:

- **VPN and networking:** WireGuard, AmneziaWG, ZeroTier, strongSwan/IPsec, EoIP, Shadowsocks local/redir, TPROXY, IPSet, QoS, IMQ, IFB, SFE and FQ-CoDel.
- **DNS and TLS:** Stubby, DoH proxy, Privoxy, OpenSSL 3.5, curl, QUIC support, HTTPS administration and DDNS over TLS.
- **Administration and tools:** Dropbear SSH, WPA supplicant, iPerf3, tcpdump, socat, ndisc6/rdisc6, Lua and QR encoding.
- **USB and storage:** USBIP, USB printer sharing, HID, NTFS-3G, filesystem tools and zram.
- **Wi-Fi and interface:** Band Steering integration (off by default), local Wi-Fi QR previews, vendor logo, Ukrainian and Russian translations.

Commented options are excluded. CAKE/SQM, TOR and ZAPRET are excluded from the current profile. Package selection and successful compilation do not prove device operation; Linux 4.4 router runtime verification is still pending.

## Build and download

Fork the repository, edit `configs.build/wr1200js.config`, then run **Actions → Build selected router firmware → Run workflow → wr1200js**.

Download the artifact named after the firmware image: its ZIP contains the **`.trx` firmware and the build configuration**.

WR1200JS is the active target. Mi Mini and Mi 4 profiles are pending; other boards are available as [upstream references](reference/boards).

## Sources and offline builds

Source revisions are recorded in [sources.lock.json](sources.lock.json). Complete offline source preservation and a verified WSL 2 build command are final project deliverables; the offline instructions will be added here after verification.

See [project scope](docs/PROJECT-DELIVERY-SCOPE.md) for remaining work. Upstream licenses apply to their respective components.
