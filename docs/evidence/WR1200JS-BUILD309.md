# WR1200JS test build 309 — integrated EoIP settings and observations

[Full run 38791149732](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38791149732)
and [service CI 38791149549](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38791149549)
succeeded at `82bee9f674216f760d913b4373d34603de59c60f`.
The full job's EoIP ROMFS verification step passed. Additional isolated
experimental candidate compilation was skipped by its optional selector;
this does not skip the selected module/controller in the actual firmware.

Artifact `WR1200JS_4.4.198.9-309_82bee9f6_TEST` (ID 11999894431) was
downloaded into `../build309-final`. Independent SHA256 and sizes:

- `WR1200JS_4.4.198.9-309_82bee9f6.trx`: 12,620,543 bytes;
  `97423fa0673920916741ec0cfa559906d2b8839a5de148c77676e392d76a4f3d`.
- `SETUP_WR1200JS.txt`: 36,694 bytes;
  `641f73e187b8e91766c90041d34dd194355f77159f312374c666735fab7c2c7e`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The configuration is byte-identical to configs.build/wr1200js.config. The
guide names build 309 and its full commit and contains the current EoIP editor,
disable and RAM/persistence instructions.

Local ZIP `../WR1200JS_4.4.198.9-309_82bee9f6_TEST.zip` contains exactly these
three files and passed ZIP CRC verification. Size 12,583,074 bytes; SHA256
`35478997b7f5d325f6d02aff60b90291974b2f86b843d6a8501cfe8e40f04641`.
The ZIP hash is for the locally assembled container, not GitHub's container.

## Compiled image evidence

Downloaded `eoip-image-checks` artifact 12000672723 is preserved as
`EOIP-BUILD309-IMAGE.json`: SHA256
`311f03d90b40cef9618301028046789bed802ddc96ff284c6d79913875fd6974`.
It records 211 structural checks: exact page/JS/script identity, navigation,
EN/UK/RU key coverage, linked HTTP/worker/default markers and executable files.
It explicitly records runtime_verified=false.

The downloaded route report is preserved as WR1200JS-BUILD309-ROUTES.json:
SHA256 `4fdfcb8dd25026a12af2c636080edfcf4328b0ec722ea57cfbd7e70af64a431e`.
All 259 served files have routes, with no assumed-undefined macros or unrouted
files. EoIP ASP matches **.asp* and both new JS assets match **.js. Route
coverage does not execute a logged-in browser session.

This image contains EoIP requested defaults, owned lifecycle/controller,
libshared-linked locked NVRAM snapshots, background observations, safe-session
POST/token settings, EN/UK/RU editor, independent rc Apply and topology/ownership
preflight before disrupting existing slots. CI exercises mock transports,
mock NVRAM/HTTP/DOM and real read-only runner netlink observations. It does not
establish remote interoperability, real frame transfer, physical MTU/keepalive,
flash persistence, reboot recovery or safe behavior under actual router load.

No router flashing, reboot, settings mutation or tunnel creation was performed.
Browser visual inspection of a local mock was blocked by the file:// URL
policy and is not counted as passed. EoIP and overall Linux 4.4.198 device-port
acceptance remain open. The wider agreed IoT/Wi-Fi/WAN/service scope remains.
