# WR1200JS test build after ABI 395

- Base: 7c4a4dff8e652a5686e8d811d0e2f850da7abc95 (ABI 395 passed).
- Preserve the merged LF normalization, authenticated JSON catalogue route, scheduled RSSI collection and httpd idle timeout fix.
- Preserve Stubby generated-configuration and QEMU authenticated DoT runtime checks. Device boot, clock and tunnel recovery still require router verification.
- Exclude IoT source integration from this device test image. Shared Wi-Fi and steering remain included, factory OFF.
- EN/UK/RU resources remain selected; existing DNS page translations and settings-backup gate stay enabled.
- Isolated candidate recompilations require explicit run_candidate_checks=true. Production preparation and image gates remain mandatory on every fresh source checkout.
- Do not claim stability before on-device testing.
