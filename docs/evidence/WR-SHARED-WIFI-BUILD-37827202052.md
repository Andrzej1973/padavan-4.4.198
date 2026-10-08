# WR1200JS shared Wi-Fi build evidence

[Run 37827202052](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37827202052) completed successfully. The downloaded diagnostic image was inspected on 2026-10-08.

- TRX: 13,096,738 bytes; SHA-256 `ab74e1fa04f9cae4c85afc1ffae1d02b672edec9b854ef66d6f9579c8a0a17f1`.
- The actual ROMFS verifier passed: exact shared Wi-Fi JavaScript, both radio pages, one shared-settings selector per page, advanced-settings toggle and hidden-row CSS, request preparation before submission, and EN/UK/RU strings.
- Retained `wifi-qr-image.json` reports all checks true for the renderer, payload and preview assets, both radio pages, and translations.
- Retained Band Steering status report passes image checks. Runtime verification remains false.

This proves compilation and image inclusion. Full legacy page behavior, live settings application, radio stability, phone connection and device support remain unverified. IoT lifecycle, DHCP, firewall and WebUI integration are still pending; this build does not provide a finished IoT network.
