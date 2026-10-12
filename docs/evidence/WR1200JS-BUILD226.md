# WR1200JS test build 226

[Run 38272210727](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38272210727) completed successfully at commit `64fa50ba`. It includes observed ZRAM swap state, DNS process labels, client-collection failure stages and build identity. DNS labels explicitly do not infer functional resolver/TLS health from process presence.

Downloaded final artifact `WR1200JS_4.4.198.9-226_64fa50ba_TEST` contains:

- `WR1200JS_4.4.198.9-226_64fa50ba.trx`, 13134891 bytes, SHA-256 `341d2721faa2a86d4cef4267a841979bfe26eb39fd08e71291c6b9e11745f1b7`.
- `wr1200js.config`, SHA-256 `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.
- `SETUP_WR1200JS.txt`, 17850 bytes, UTF-8 decoded successfully; SHA-256 `ea526411817efdcb33c80778702caeb0a18e7bc4d57c7c84dd978337d3abe4ba`. Its identity matches the image suffix.

[Native state checks 38272444310](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38272444310) passed ASan/UBSan execution of the emitted DNS handler and ZRAM status/lifecycle checks. Image packaging and compilation do not establish live WebUI behavior, functional DNS lifecycle, ZRAM activation or sustained router stability.

The router was last observed on `4.4.198.9-100_shmily`. Stubby/DoH are intentionally disabled following the earlier jointly investigated outage. No flash or live service changes were performed during this verification. Other service/driver status adapters, functional DNS health and broader delivery requirements remain pending.
