# WR1200JS test build 315 — independent WAN selector

Full run [38840408246](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38840408246)
succeeded at `78efe0d6cdfd7e1c145f77951af5679f2f02d883`.
This is an intermediate image: it predates effective-WAN link-status correction
177d37a, the WAN ROMFS gate fb54199, and ZeroTier cache semantics bdf1d5d.
It is not evidence that the current main image has finished building.

Downloaded artifact 12021576257, `WR1200JS_4.4.198.9-315_78efe0d6_TEST`,
into `../build315-final`. It contains exactly three files:

- TRX: 12,622,039 bytes, SHA256
  `89e805d9c26f1bdfb42a248b378b0016b54ca731f4b472dcef3f6977944722bb`.
- SETUP_WR1200JS.txt: 38,286 bytes, SHA256
  `d322c8bcf77a4e2b95759d8ad3f5287e4fbf4a3cfeab2535881df0807627fb0d`.
- wr1200js.config: 11,333 bytes, SHA256
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The packaged profile is byte-identical to configs.build/wr1200js.config.
The guide passes check-router-guide.py. Regenerating from the downloaded
firmware-effective.config reproduces the exact text after LF/CRLF normalization
(Linux artifact LF, local Windows output CRLF). Generating from the raw profile
does not reproduce the guide: CI correctly uses normalized effective service
flags. No byte-identity claim is made for the local CRLF guide.

Downloaded ZeroTier report artifact 12021267553 into ../build315-zerotier;
SHA256 `7b7401aadba9dce949558b42eefdc8536c1b7aadeedcfb6370c38b51b0f98a63`.
All seven checks are true, errors empty, runtime_verified=false. It records
source-built 1.16.2, executable SHA256
`594fbca15fc8416f4c4dd52cca43068f28968d2c702db539d4dff6bc4e0f8270`,
dependency closure, lifecycle/monitor/policy, WebUI, defaults/firewall guards
and persistence assets. This supersedes older documentation saying production
image integration has no build evidence; it does not prove live operation.

No flashing, restart, WAN reassignment or ZeroTier mutation on the router was
performed. Physical socket mapping, connectivity, isolation, persistence and
runtime acceptance remain open.
