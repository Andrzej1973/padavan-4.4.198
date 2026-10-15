# WR1200JS test build 283 — USB/IP actions and results

[Full run 38746682565](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38746682565)
passed at `31a649681f63e7847dbbe41f58fa99523ac6d67a`.
Artifact `WR1200JS_4.4.198.9-283_31a64968_TEST`, ID `11978493821`, was
downloaded into `../build283-final` on 2026-10-15.

Independently computed SHA256:

- TRX `WR1200JS_4.4.198.9-283_31a64968.trx`: 12,600,515 bytes;
  `eac3ec48fc67386e83c73758347ab64c3d607e26467a6eeff87d8b054ff31060`.
- `SETUP_WR1200JS.txt`: 28,865 bytes;
  `5f79ebc5564f62cba1bf9228bd2be229019300982bce2ae6b421a3c113611bd6`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The config hash matches the requested profile. The guide contains the exact
build/commit and instructions for selecting, confirming and observing a USB
action. This image includes the controller/preflight, inventory, background
executor, HTTP POST/token guards, action UI and EN/UK/RU text. Its image gates
check script equality, handler/route strings and page/dictionary markers;
they do not execute the running HTTP server.

[Service run 38746682477](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38746682477)
passed at the same commit. Log entries confirm actual execution of the native
background-job and HTTP-action fixtures, plus the Node action-view fixture.
The job tests execute a mock controller, the HTTP tests mock scheduling, and
the UI test mocks AJAX/DOM. They do not prove a live authenticated browser
session or a real USB transfer.

A local delivery ZIP was created from exactly these three downloaded files:
`../WR1200JS_4.4.198.9-283_31a64968_TEST.zip`, 12,561,439 bytes,
SHA256 `93b23d3268fe26c432955539a990e88eca2cd0db2416cae730d9448fffcff9fd`.
Python zipfile verified CRCs and the exact three entry names. This local ZIP
hash identifies the locally assembled container, not GitHub's artifact ZIP.

No flashing, reboot or USB action was performed on the router. Browser
rendering, safe-session behavior, real devices/driver races, LAN-only access,
USB transfer and reboot/export persistence remain unverified. Automatic
restoration of selected USB exports is not implemented. Overall device-port
acceptance and the remaining agreed project scope are still open.
