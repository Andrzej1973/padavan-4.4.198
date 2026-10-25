# WR1200JS isolated IoT v40 target compile — build #600

GitHub Actions run [#600](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40216625327)
completed successfully on branch `codex/wr1200js-service-webui`, HEAD
`a71e8abedf4c2a6c1fd5df2917002db990df84e2`, attempt 1. The run was dispatched
with the optional candidate checks enabled and `iot_candidate_variant=v40`.
Both `Build WR1200JS firmware` and `Compile isolated merged IoT MT7603
candidate` succeeded.

## Target artifact

The `iot-merged-driver-probe` artifact (GitHub artifact ID `12607858175`,
2,038,264-byte ZIP) contains `mt76x3_ap.ko` and its complete candidate build
log and metadata:

- Module size: 5,202,152 bytes.
- SHA-256: `f01a3272ac60769dd08a312fbe67622284fa590a533285335a749a300b75a4e5`.
- ELF: ELF32, little-endian, relocatable MIPS, O32, MIPS32r2.
- Source: pinned MediaTek tree revision
  `c25283e915a2a00a763774dd255b14aff997285e`; 58 candidate overlay paths were
  assembled against the prepared tree before compilation.
- Target compile log ends with `LD [M] .../mt76x3_ap.ko` followed by successful
  `make` exit.

For comparison, build #595's earlier isolated `mt76x3_ap.ko` was 5,200,856
bytes with SHA-256
`2be70edfa1dd9eaa9402560000111f89657d456134072e91cc4b6d5e874a2039`. The v40
module is 1,296 bytes larger. This is an uncompressed module-file comparison,
not an estimate of firmware image growth.

## Warning and evidence boundaries

The candidate build log reports one non-fatal kernel `modpost` warning:
`Found 1 section mismatch(es)`. The log does not identify the specific symbol;
its source and whether it predates v40 are therefore unresolved. This warning
did not fail the module link. Investigate it with detailed section-mismatch
diagnostics before production integration if it is attributable to the overlay.

The artifact's source manifest keeps `target_compiled=false` as source-package
metadata; the separate successful target build log, MIPS ELF header and module
artifact are the compile evidence. The workflow compiles this probe after the
ordinary firmware image is built, so this candidate is **not included in the
#600 firmware image**. No production driver, final ROMFS, router or runtime
behavior was validated by this candidate step. In particular, the MCU command
result plus PDMA readback does not prove RF silence, callback quiescence, safe
main-interface close, safe PCI removal, IoT isolation, or live third-BSS
operation.

## Next gates

1. Explain the `modpost` section mismatch without assuming it belongs to v40.
2. Bind checked main stop to an adapter-pinned recovery owner; the current
   `MainVirtualIF_close` still releases its module pin without physical-close
   proof.
3. Bind child/root teardown, callback quiescence, worker stop/join and the
   adapter-release gate into PCI remove, including persistent failure behavior
   for its `void` callback.
4. Re-run the isolated target compile after any source integration. Only after
   those lifecycle gates pass should candidate image packaging and final-ROMFS
   checks begin; device acceptance remains a separately authorized stage.

No router settings, firmware or runtime services were changed.
