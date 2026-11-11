# WR1200JS final WebUI release variants

Owner requirement recorded 2026-11-11: produce two final firmware variants:

1. **Modern + Classic**: complete Modern WebUI with Classic also available.
2. **Modern only**: complete Modern WebUI without Classic pages/assets.

This is a final delivery requirement, not permission to remove Classic during
unfinished development. Both variants must retain mandatory IoT, Band Steering,
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

Publish both clearly named firmware assets with their checksums and variant
descriptions. The existing standard/optional CI verification lanes are not
these release variants; track variant and verification lane independently.

Status: requirement recorded; variant build selection, Modern-only completeness,
matched image comparison and both release acceptances remain pending.
