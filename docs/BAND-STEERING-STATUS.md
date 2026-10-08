# WR1200JS Band Steering controls and status

This is an experimental integration for the MT7603E + MT7612E WR1200JS profile.
The firmware includes the service, but its requested setting is **disabled by default**.
A successful build does not establish operation on the router or client roaming behavior.

## Settings

The coordinated **Band Steering (2.4 GHz + 5 GHz)** setting is on the 2.4 GHz advanced wireless page. It controls both radios; the legacy 5 GHz steering selector is hidden.
Use the same SSID and compatible security on both main networks. Guest networks are excluded. This feature does not establish 802.11k/v/r support.

Changing the selection and applying the form uses the existing Wi-Fi apply mechanism and can interrupt wireless connections. The saved selection expresses the requested state; it is not proof that the service is running. Incompatible settings or an unavailable radio prevent activation while preserving the user's saved request.

## Refresh status

**Refresh status** schedules a read-only rc observation. It does not apply settings, restart Wi-Fi, or activate the service. The page waits for a changed observation serial and stops after six polling attempts; each HTTP request has a three-second timeout. There is no automatic background refresh.

- **Daemon reports ACTIVE:** the owned daemon answered an authenticated control request. This is not a new driver readback or proof of client steering.
- **Last verified OFF:** rc holds the last successful OFF confirmation. This is not a fresh driver-state measurement.
- **State unknown:** no fresh confirmation, failed request, unavailable daemon, or invalid response. A missing process/socket alone never establishes OFF.

English, Ukrainian, and Russian labels are supplied. Browser rendering and hardware behavior still require verification.

## Evidence and outstanding checks

- [Status observer and HTTP fixture CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37782250557): passed host sanitizer execution and target compilation of extracted handler fixtures.
- [Complete 22-step source integration CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37783377647): passed source preparation, target package and status UI checks. This is not a complete firmware or device test.
- The former default insertion was inside the MT7615/MT7915 conditional and was absent from the actual WR1200JS library. Commit `45791afe4c4e2f14692d2daa70889001543e9474` places the coordinated OFF default in the unconditional defaults array and uses the actual Padavan `char **` HTTP signature.
- [Factory-OFF regression CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37787756190): passed. It preprocesses the real defaults source for MT7612/MT7603 and confirms that reproducing the former conditional placement removes the key.
- Full-image verification checks page bindings, the exact JavaScript asset, language keys, and compiled HTTP/rc string presence. These checks do not prove runtime operation.

Complete firmware build and actual ROMFS checks passed for [run 37787484281](evidence/WR-IMAGE-37787484281.md). That revision precedes the wireless HNAT changes. Pending: rendered-page verification and recoverable on-device tests. No router flashing or reboot is performed by these build checks.
