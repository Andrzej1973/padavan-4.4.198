# ZeroTier WebUI and lifecycle image evidence

Observed 2026-10-04 in [run 37175104110](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37175104110), build number 20, source `a91d8bd4b53c5d42e837dfebbe1552f929b6ba43`, job `111356014784`.

The WR1200JS firmware build, requested/effective configuration, image structure and expanded ZeroTier image gate passed. The image was uploaded. The complete workflow was still running isolated package candidates when this evidence was collected; overall completion is not asserted here.

Downloaded artifact `11293641364` (`zerotier-image-checks`) reports all six checks true:

- Pinned ZeroTier source version/revision and ROMFS executable code match.
- Target ELF and recursive shared-library dependencies are present.
- Lifecycle helper exists.
- Lifecycle, monitor and policy scripts match source bytes and pass shell syntax.
- Network/permission/leave controls and the compiled cached-status HTTP handler are present.
- ZeroTier and router/LAN access factory defaults are zero; compiled rc contains the overlay firewall guard chains.

The JSON `errors` list is empty and `runtime_verified` is false. Diagnostic ZIP SHA256: `c0a46affd009c42a92bb57760d261ce9d8b487e46d7072f3d5bdfefbf2469df2`.

ZeroTier executable SHA256 remains `594fbca15fc8416f4c4dd52cca43068f28968d2c702db539d4dff6bc4e0f8270`.

The storage persistence changes from later commit `7b9d8b8d9831c106c02d235f463fa7b9d49a9270` are not included in this run; they are being built in run 37175711374 (number 21).

This proves compilation and image packaging. It does not prove WebUI rendering on a router, service lifecycle, controller authorization, packet forwarding, firewall restart behavior or persistence after reboot/upgrade. No physical router flash or reboot was performed.
