# Final release matrix update

## Four final WR1200JS variants before Mi Mini — owner requirement 2026-11-17

Complete and verify four final Hybrid Modern images with all agreed fixes:

| Variant | Hybrid Modern | Classic | CAKE/SQM |
| --- | --- | --- | --- |
| 1 | Included | Included | Included, factory OFF |
| 2 | Included | Omitted | Included, factory OFF |
| 3 | Included | Included | Omitted |
| 4 | Included | Omitted | Omitted |

Mandatory IoT, Band Steering, Zapret2, settings compatibility and router access
remain requirements in all four. Included CAKE must support explicit enable/
disable from the available WebUI, including the variant without Classic.
CAKE-free images must omit the implementation and expose no working-looking
CAKE control. Existing saved settings must be preserved across variants;
CAKE factory OFF must not silently overwrite an owner's saved enabled choice.

This supersedes the earlier two-image delivery matrix and mandatory CAKE in
every final image. Keep CAKE included/default OFF in the current development
baseline until explicit final variant selection is implemented. It does not
resume paused Modern development or authorize router changes.

Verify each image independently: exact revision/toolchain/configuration,
TRX size and SHA256, ROMFS, feature inclusion/absence, complete WebUI controls,
release gates and separately authorized physical acceptance. Compare Classic
size at fixed CAKE selection and CAKE size at fixed Classic selection using
matched builds. CI standard/optional lanes remain separate from release variants.
**Only after WR1200JS acceptance, including this four-variant delivery, proceed
to Mi Mini.** No completed images or device acceptance are claimed by this rule.

# WR1200JS final WebUI release variants

Historical WebUI axis recorded 2026-11-11 (expanded to four final images by the
2026-11-17 CAKE axis above):

1. **Modern + Classic**: complete Modern WebUI with Classic also available.
2. **Modern only**: complete Modern WebUI without Classic pages/assets.

This is a final delivery requirement, not permission to remove Classic during
unfinished development. All four variants must retain mandatory IoT, Band Steering,
Zapret2 and the other agreed firmware features, with the same settings
compatibility, safety and release gates. Existing Classic-only development
controls or fallback links are not sufficient for the Modern-only release.

Before releasing Modern only, verify complete page/function coverage in Modern,
including IoT, authentication, configuration save/apply, recovery and maintenance.
Keep shared HTTP/CGI handlers, libraries and resources required by Modern or
other firmware functions even if historically associated with Classic. Audit
navigation so no required function leads to an omitted Classic page. Verify
each variant's final ROMFS and device behavior separately under the project's
explicit device-authorization policy; a successful build is not runtime acceptance.

For the size comparison, build both variants from the same source revision,
toolchain, board configuration, feature set and compression settings, with
only the WebUI variant differing. Record each exact build input, final TRX byte
count and SHA256, ROMFS contents, and the byte/percentage difference between
the images. Report build metadata or other unavoidable differences explicitly.
Do not equate uncompressed Classic source size with space saved in the
compressed firmware. Determine actual savings from the matched final builds.

Publish all four clearly named firmware assets with their checksums and variant
descriptions. The existing standard/optional CI verification lanes are not
these release variants; track variant and verification lane independently.

Status: requirement recorded; variant build selection, Modern-only completeness,
matched image comparison and all four release acceptances remain pending.
