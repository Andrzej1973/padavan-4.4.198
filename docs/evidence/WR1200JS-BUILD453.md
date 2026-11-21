# Build 453 final guide/image binding — 2026-10-18

[Run 39115129564](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39115129564)
completed successfully for `005c74974a456dc156fa1765a00b382180611935`.
Downloaded final artifact ID `12132386084` contains exactly:

- `WR1200JS_4.4.198.9-453_005c7497.trx` (12621503 bytes).
- `wr1200js.config`.
- `SETUP_WR1200JS.txt`.

Independent SHA-256 of the TRX:
`1a07cae6b299583539778877eff876052e0c210bc929f967349f778bf298c7eb`.
`tools/bind-router-guide-image.py --check` passed against the downloaded
guide and TRX. The final guide therefore contains the exact image filename
and digest; this closes the missing identity found in build 451's guide.
Independent uImage checks also passed; see `WR1200JS-BUILD453-STRUCTURE.json`.

This verifies final artifact contents and guide binding. It does not establish
device boot, persistence, service lifecycle or completion of the firmware port.
The stronger final-staging refusal in `f9b0616` postdates this build and still
requires its own CI result.
