# WR1200JS build 454 — image and IoT capacity evidence

[Run 39115399372](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39115399372)
completed successfully for commit `594d98b61af7c0a62af9ceb26dd43849e57171df`.
The independently downloaded image artifact was `12132218030`.

- Image: `WR1200JS_4.4.198.9-454_594d98b6.trx`.
- Bytes: `12621707`.
- SHA-256: `7a25388b2838a567dc61b4be179ebbc07f8162eebec1cb029d488a42eec31cfe`.
- The local image verifier passed uImage magic, WR1200JS product ID, header and
  payload CRCs, declared length and upload-size range. Detailed output is in
  `WR1200JS-BUILD454-STRUCTURE.json`.
- `bind-router-guide-image.py --check` confirmed the generated setup guide
  contains this exact image filename and digest.
- Downloaded target Kbuild capacity evidence reports effective source/config
  limits of 16 BSS for MT7603 and 8 for MT7612. The required three-BSS
  source/config gate passed for the 2.4 GHz MT7603 radio. Reports are in
  `WR1200JS-BUILD454-IOT-MT7603.json` and
  `WR1200JS-BUILD454-IOT-MT7612.json`.

These checks establish image structure, guide identity and source/configuration
radio capacity. The capacity reports explicitly set `runtime_verified: false`;
they do not prove that the driver creates a working third BSS. The BSS-UP
primitive is compiled and covered by CI, but production radio reload/activation
is not integrated. No physical device boot or runtime test is claimed.
