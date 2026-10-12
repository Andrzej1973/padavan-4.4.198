# WR1200JS test build 219

[Run 38171596542](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38171596542) completed successfully on commit b642bd6. The board build, downloads and firmware-zip jobs all passed. Build 218 also completed successfully following the Shadowsocks guide selector correction.

Downloaded final artifact `WR1200JS_4.4.198.9-100_TEST` contains:

- `WR1200JS_4.4.198.9-100.trx`: 13133319 bytes; SHA-256 `21c1859d32f583a910f956099049bbd1d6c03b4c49d8234d76ad5ea5b5dada2f`.
- `wr1200js.config`: SHA-256 `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.
- `SETUP_WR1200JS.txt`: 17709 bytes; UTF-8 decoded successfully; SHA-256 `a02a69ad0ef39f44404cfd012d5290b4502df915d8deba3c9ae1451cf493d4af`. Shadowsocks, ZeroTier and Stubby sections are present.

[ZRAM lifecycle check](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38171596533) passed native ASan/UBSan execution of functions extracted from the patch with mocked system operations. Build 219 verifies integration and image dependencies. These checks do not establish router swap activation, boot lifecycle, preserved management access or sustained stability. No router flashing or configuration changes were performed for this verification.
