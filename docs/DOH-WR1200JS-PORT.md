# DoH port for WR1200JS Linux 4.4.198

Central DoH=y previously lacked a prepared target mapping: run37139627972 failed specifically on this selector. This port uses the exact preserved donor archive (MIT), not Stubby or generic dnsproxy. See sources/https-dns-proxy.lock.json for provenance; the donor filename does not independently identify an upstream commit.

Added build selector, libcurl/c-ares/libev dependencies and target O2 CMake build; preserved all ten doh_* defaults with enable=0. Existing stored NVRAM is not rewritten. Supports four HTTPS URLs, inherited resolver catalogue/custom URLs, standalone/dnsmasq modes, loopback/LAN/all-IPv4 listeners, bootstrap DNS and HTTP/3 option. Explicit pinned CA bundle, verified PID ownership, restart lock and startup rollback are used. BusyBox readlink is enabled only by this selected port.

Includes boot/shutdown/restart/NTP clock-step handling, extended HTTP event bit1, escaped value/capability hooks, settings and menu/page. dnsmasq mode disables ordinary upstream resolv fallback and preserves the donor's domain-scoped NTP bootstrap exception.

Image gates inspect selector, MIPS binary/all ELF dependencies/loader, helper syntax and executable mode, CA hash, license, resolver catalogue, WebUI/backend/rc presence and disabled factory default.

Python syntax and a prepared-source transformation were checked locally. The first minimal library fixture lacked full base anchors; the successful transformation used the exact pinned complete library Makefile. Shell syntax was unavailable locally and is checked in the image gate. Full cross-compilation, image gates and browser/runtime behavior are pending. The existence of selectors or source files does not establish DoH functionality.

After compilation, verify encrypted DNS/HTTP2 and optional HTTP3, certificate rejection, time bootstrap, outages, multiple instances, listener modes, saves/restarts/reboot persistence on a device with recovery available. No router flash or reboot was performed.
