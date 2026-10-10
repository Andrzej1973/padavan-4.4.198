# WR1200JS build 147: RSSI candidate compile evidence

[Build 147](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38041159759) and its actual isolated full-driver compile step completed successfully on firmware source commit `158c941a23f4a371048606da6b0f0b90de4e874c`.

The log records adapter storage, station birth identity, RSSI decision/allocation/frame submission and matched entry-clearing preparation before compiling both complete driver modules. Downloaded diagnostics contain ELF32 MIPS modules and symbol tables with `wr_rssi_delete_entry` in each. Their downloaded bytes match the recorded hashes:

- `mt76x2_ap.ko`: `eb339c45564861debbbba6c61c18163fca692f3a11ea2c2785960f6a8f6df60e`.
- `mt76x3_ap.ko`: `65242d1940b45c822cddd324ff5bb726bd55bdbc00891493f8ca39d964e85b5a`.

This is complete candidate-driver compilation evidence. The isolated modules are diagnostic artifacts, not installed in the normal TRX. RSSI query transport, adapter-session handling, authenticated collection and WebUI RSSI events remain incomplete. No router boot, wireless stability, kick, reassociation or tunnel recovery is established by this result.

[ABI 302](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38041240131) also completed successfully. Runtime validation remains required.
