# WR1200JS test build 266

[Run 38606215467](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38606215467),
commit `c1fbc585b9182cecb42520719b54f0562b67f8f5`, completed successfully.
Artifact `WR1200JS_4.4.198.9-266_c1fbc585_TEST`, ID `11916321896`, was
downloaded to the parent workspace's `build266-final` directory.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-266_c1fbc585.trx`: 12,588,838 bytes;
  `aabf9b20a7a091b82cc4194ee3a866020553ad4e433ed26b7867e850a46fc5bb`.
- `SETUP_WR1200JS.txt`: 23,353 bytes;
  `7d0db50c7b1cb10319c14a749f7ebd83e4b66facc0a647258605814530076ef5`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

This build includes profile gating of the USB/IP observation panel and unknown
module state when `/sys/module` is inaccessible. Later emitted-JavaScript and
native endpoint tests are separate evidence, not part of this commit.
Physical installation and runtime behavior of this image remain unverified.
