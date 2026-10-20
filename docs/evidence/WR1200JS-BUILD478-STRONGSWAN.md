# WR1200JS StrongSwan exclusion checkpoint — 2026-10-18

Build #478, GitHub Actions run
[39139346947](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39139346947),
used source commit `d1dc0ebaf82af316ad8ba65a01952c229c69e919` and completed
successfully. The requested WR1200JS profile comments out
`CONFIG_FIRMWARE_INCLUDE_SSWAN=y`; XFRM remains independently selected.

The main final-image policy gate in the firmware build requires StrongSwan to
remain disabled in the effective configuration and checks the absence of
`ipsec`, `charon`, `starter`, `stroke`, `libstrongswan.so.0` and
`libcharon.so.0`. Because the selector was disabled, the separate positive
StrongSwan package verifier did not run, and build #478 has no
`strongswan-image-checks` artifact. Therefore this checkpoint is based on the
successful main image-policy gate, not a dedicated archived exclusion report.

The workflow now generates a report for both profile branches: package and
dependency checks when selected, or requested/effective selector plus ROMFS
absence checks when deferred. Artifact upload now fails when that report is
missing. The dedicated exclusion report will be available from the next build.

This does not provide StrongSwan WebUI or runtime acceptance; the service
remains intentionally deferred. It also does not remove or disable shared XFRM
kernel facilities. No router state was changed.
