# WR1200JS Padavan Modern design references

These images were supplied by the project owner as visual references for the
Padavan Modern WebUI. They are design mockups, not screenshots proving current
router capabilities or runtime state. All IP addresses, clients, service
states, temperatures and logs shown in them are demonstration values.

## Files

| File | Intended reference |
| --- | --- |
| `dashboard-neon-uk.png` | Ukrainian neon dashboard with the overview of all planned pages. |
| `dashboard-neon-uk-detailed.png` | Larger dashboard/service-state alternative. |
| `wifi-shared-settings.png` | Shared 2.4/5 GHz settings with separate and IoT entry points. |
| `wifi-split-settings.png` | Split 2.4/5 GHz settings with the IoT card. |
| `wifi-general-24.png` | General 2.4 GHz settings with channel, advanced features and QR actions. |
| `wifi-bridge-24.png` | 2.4 GHz WDS bridge, client and AP scan layout. |

## Integrity

```text
a06fefb02d09d61d620db9c35e424c256a5cb46895f9e4b4b5793d8164379b84  dashboard-neon-uk-detailed.png
b53d077079c35179fd7ca0478902f0f2150ad13a656b5eccfb4df08ac57fb520  dashboard-neon-uk.png
c6a6ef94307fd329f53fdaec23f6f9f4f531163a7a678ba0677b14257685f092  wifi-bridge-24.png
b73622f2f4367a53c765fe26eeca4555e9df668d43bd38c21e7ee8771470f937  wifi-general-24.png
c1394ebc7b34db172f7d090d7c4954e6555b5803e064de5f7194f75c48229b03  wifi-shared-settings.png
c06967e3b3cfcc26f31ef153c23984d8369e89787945bce415d207770a2c677b  wifi-split-settings.png
```

## Required boundaries

- Keep Padavan Classic as the working production interface until the Modern
  implementation has separate image and device evidence.
- Do not add an IoT card as a live network until the WR1200JS IoT lifecycle,
  DHCP/firewall isolation and device acceptance are complete.
- Render unavailable hardware features as unavailable; do not reproduce mock
  values as measurements.
- The preview must remain local, read-only and clearly marked `DEMO`.
