# WR1200JS build #539: IoT beacon-lock probe

- GitHub run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40010959461
- Run conclusion: success; branch commit: `9727933066f158bb063292418e150e5f6fd1eec2`.
- Downloaded artifact: `wr1200js-iot-radio-capacity/mt76x3.json` (local copy under `artifacts-539/`). SHA256: `964954c833252d1b6dd9e8fb40d416890149ea21bf0f11d11247c12fed5a571f`.

The artifact reports `probe_status=complete`, effective MBSS support, and a
source/config limit of 16 BSS. These are build/source facts, not live IoT BSS
acceptance. `main_observer_probe` is null because the corresponding workflow
addition remains local and was not part of this run.

All four `beacon_lock_units_probe` units (`ap/ap_cfg.c`, `ap/ap_nps.c`,
`common/cmm_data_pci.c`, `common/cmm_mac_pci.c`) were **unavailable**. GCC
directive output contained byte `0xa1` that Python's strict UTF-8 text mode
could not decode. Consequently, `active_after_directives` and each unit's
`effective_multi_core_support` are null. The seven source-text lock sites
remain an inventory; this run cannot select a safe production lock form.

The probe now decodes directive output with UTF-8 `surrogateescape`, preserving
ASCII line markers and lock calls while tolerating legacy comment bytes. A
synthetic subprocess regression case emits invalid byte `0xa1` between a
target file marker and lock call. The full capacity self-test, Python syntax
check, and diff whitespace check passed locally after the change. Exact
WR1200JS per-unit results require a subsequent build artifact. No driver,
image installed on a router, or router state was changed by this fix.
