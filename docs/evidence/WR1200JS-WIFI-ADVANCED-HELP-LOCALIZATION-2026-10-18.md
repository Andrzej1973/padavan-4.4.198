# WR1200JS advanced Wi-Fi labels and help localization — 2026-10-18

The supplied screenshot shows the 5 GHz advanced wireless page with English
labels for AMSDU, 802.11KV, 802.11R, MU-MIMO and Transmit Beamforming while the
surrounding controls are Ukrainian.

Inspection of saved build #410 shows that `WLANConfig11n_80211kv` and
`WLANConfig11n_80211r` have English values in `EN.dict` and Russian values in
`RU.dict`, but no Ukrainian values in `UK.dict`. The inherited dictionary
transform now adds exact EN/UK/RU values for both keys and the existing image
verifier checks them alongside other inherited dictionary entries.

The hover help for the retained controls is loaded by `help_wl.js` through the
localized dictionary keys `WLANConfig11n_amsdu_itemdesc` and
`WLANConfig11n_mumimo_itemdesc`. Transmit Beamforming is not localized because
the board capability audit found its driver option disabled; its misleading
control and help entries are removed from the WR1200JS build preparation. A new
image and browser review are still required to confirm the retained help text
on the running router. No firmware was built or flashed and no router setting
was changed for this update.
