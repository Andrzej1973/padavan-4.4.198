# WR1200JS wireless bridge help localization — 2026-10-18

The supplied screenshot of Wireless → Bridge (5 GHz) showed two inherited
dictionary strings in English under the Ukrainian interface: the
`AP_Relay` link that opens the wireless relay enhancement script, and the
`AP_Relay_1` description of its automatic signal/channel selection.

The available build #410 EN dictionary contains both values in
`EN.dict`; UK and RU do not define these keys, so those locales fall back to
English. `overlay/padavan-4.4/scripts/localize-inherited-dicts.py` now replaces
the exact inherited English values and supplies translated EN/UK/RU strings.
The source guard checks the original strings before replacement, and the
existing image-verification path checks every `ENTRIES` value against the
corresponding final dictionary.

This change affects help text only; it does not change bridge mode, repeater
script behavior, Wi-Fi settings or Apply handling. No tests or firmware build
were run for this update. Final-ROMFS verification and browser review in the
Ukrainian and Russian locales remain pending. No router state was changed.
