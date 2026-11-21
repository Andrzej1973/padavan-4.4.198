# WR1200JS USB/IP image checkpoint — 2026-10-18

Firmware build #478, GitHub Actions run
[39139346947](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39139346947),
used source commit `d1dc0ebaf82af316ad8ba65a01952c229c69e919` and completed
successfully.

The build job completed these USB/IP-specific gates:

- **Step 56 — Check USBIP restore orchestration with exact target BusyBox:**
  success. The fixture checks default-off behavior, reader/daemon failures,
  full-batch preflight, unique serial identity, malformed identities, hotplug
  between preflight and dispatch, and partial/unconfirmed bind handling. It
  uses mocked device data and does not touch router USB devices.
- **Step 59 — Verify USBIP settings UI and linked HTTP storage code:** success.
- **Step 60 — Preserve USBIP settings image evidence:** success. Artifact
  `usbip-settings-image`, ID `12141546396`, SHA-256
  `6076fadb588f3738e4ccbf7ac62e420ad430d14ca0d3a42747e5e4a1e2921c9f`.

The ROMFS verifier checks the localized settings UI, authenticated HTTP handler,
storage path, lifecycle lock, default-off restore control and explicit
`applied:false` / `flash_committed:false` response. Thus the build supports a
source/image claim for those components. It does not prove physical-device
module loading, daemon reachability, successful export, client attachment,
data transfer, flash durability or reboot recovery.

The export table is atomically written under `/etc/storage/usbip`; a successful
directory synchronization is reported separately from a synchronization
failure, but the handler never claims an NVRAM/flash commit. Restore remains
opt-in and only binds devices after its identity and safety checks. No router
state was changed during this audit.

## Local UI fixture follow-up — 2026-10-19

Ran `node tools/usbip/check-action-view.js` and
`node tools/usbip/check-settings-view.js` against the current source; both
passed. The action fixture covers fresh inventory selection, daemon state,
confirmation, POST submission, duplicate-submit prevention, matching job IDs,
stale observations and timeout behavior. The settings fixture covers the
export-table codec, duplicate identities, confirmed save, single-flight
behavior, a separate `synchronized:false` durability warning, uncertain server
results and preservation of a dirty draft.

These host-side JavaScript fixtures verify UI behavior against mocked AJAX;
they do not establish that the assembled page behaves correctly in a browser
on the router. Build #478 remains the cited image evidence. Actual USB module
and daemon operation, bind/unbind, client attachment, transfer, storage-save
and reboot persistence remain unverified on the device.
