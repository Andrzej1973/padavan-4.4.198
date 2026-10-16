# WR1200JS test build 317 — WAN UI and effective-role link monitoring

Full run [38840756322](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38840756322)
and service CI 38840755902 succeeded at
`fb54199707a8bc37e6a774d28ce5acdc215d95db`.

Downloaded package artifact 12021692061,
`WR1200JS_4.4.198.9-317_fb541997_TEST`, into ../build317-final.
Exactly three files, with independently calculated SHA256:

- WR1200JS_4.4.198.9-317_fb541997.trx: 12,622,207 bytes;
  `07dd150308d0e53d7907070d7df7c8123937f57a47765aaf1773a3c38eee0d30`.
- SETUP_WR1200JS.txt: 38,286 bytes;
  `ffb115f0001df6d96892c2cc24e7d9b73484396de41d32ee955f3d9e7424f79d`.
- wr1200js.config: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

Profile bytes match configs.build/wr1200js.config. Packaged guide has the
correct build number/full commit and passes the guide content checker.

Downloaded WAN report artifact 12020803528 is preserved verbatim as
WAN-BUILD317-IMAGE.json, SHA256
`3206078f43ce2014fb946c443f244d6c2bdac0c3864966238aa5ff9d68eee433`.
All 15 checks passed: shipped WAN selector/help/confirmation, EN/UK/RU keys
and safe confirmation literals. Hashes identify the shipped page/dictionaries.
runtime_verified=false is explicit. This report does not execute a browser.

The image includes independent WAN selection, Apply switch-VLAN event and
effective-role link monitoring. It predates newer ZeroTier status changes and
the cde23db effective socket name/mismatch panel. Those require their own
finished image evidence. No physical flash, restart or port change was made;
socket mapping, cable moves, isolation, VLAN fallback and persistence remain
unverified on the router.
