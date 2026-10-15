# WR1200JS test build 294 — packaged EoIP controller and boot policy

[Full run 38784465385](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38784465385)
completed successfully at `6f8e33eee6f23e1e81270980365bdcfa562ad020`.
Artifact `WR1200JS_4.4.198.9-294_6f8e33ee_TEST`, ID `11998246932`,
was downloaded into `../build294-final` on 2026-10-15.

Independently computed SHA256 and sizes:

- `WR1200JS_4.4.198.9-294_6f8e33ee.trx`: 12,608,803 bytes;
  `c56daaf31a6ccd0652bfba83dd25d6e5e1f6b0da8a6f699c691efb6aaf092280`.
- `SETUP_WR1200JS.txt`: 33,111 bytes;
  `af3c86e2c7a1237beee7150c777ef3a23ab776bc7c031827aaabb56298ea40f2`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The config is byte-identical to the current requested profile. The guide names
the exact build and full commit and contains the expanded EoIP instructions,
GRE protocol clarification and read-only status-json command.

The local ZIP `../WR1200JS_4.4.198.9-294_6f8e33ee_TEST.zip` contains exactly
these three entries and passed Python zipfile CRC verification. Size:
12,570,622 bytes. SHA256:
`590e3b70f0ff8cfc60f465233c27bd5549559c265439965d6185495e276f1465`.
This is the locally assembled ZIP hash, not GitHub's artifact container hash.

This commit includes the default-off EoIP profile defaults, boot/shutdown
policy, owned worker/controller and structured command-line observations.
It predates apply-table/stop-table, the HTTP background status collector and
the localized EoIP page; none of those later features is established by this
artifact. Do not use build 294 as evidence that current HEAD has compiled.

Builds 291 (38783698201) and 292 (38784060440) were also observed successful.
Later runs were still active when inspected; they were not assumed hung or
restarted. No flashing, reboot, EoIP creation or frame transfer was performed.
Settings restoration, reboot persistence, remote interoperability, live UI and
overall physical port acceptance remain unverified.
