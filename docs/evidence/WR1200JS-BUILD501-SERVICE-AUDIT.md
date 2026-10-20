# WR1200JS build 501 — service image audit

GitHub Actions [run 39459184144](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39459184144)
completed successfully for source commit `560ee18db70cff914ccb365a1226ccc76ceeba94`.
The build job, artifact aggregation, required-board check and firmware/config
ZIP job all report success. GitHub retained the output artifact
`WR1200JS_4.4.198.9-501_6fb42af4_TEST` (12,803,015 bytes; artifact digest
`sha256:31f5c3005f249ed4514ad3a82fdd50a57f2a60e9f128e98348490fb04d21ff09`).

The completed build log confirms selected final-ROMFS checks for:

- iPerf3 requested/observed process UI, HTTP handler and EN/UK/RU labels;
- Shadowsocks text and dictionary consistency in EN/UK/RU;
- settings backup/restore safe-session rows, form routes, downloads, uploads
  and flash-save feedback;
- target BusyBox service entrypoints and the VPN/USBIP target-shell fixtures;
- Stubby image dependencies and a QEMU DNS-over-TLS query; and
- KMS/Watchdog status UI, HTTP handlers and EN/UK/RU help.

These are build/image checks, not physical-router acceptance. The iPerf3 log
explicitly leaves a client test and throughput unverified. This image also
predates the bounded iPerf3 LAN-client instructions added in `5d1385f`.

## StrongSwan report gap found in this run

The StrongSwan verification step selected the disabled-service branch, but the
old workflow did not create `strongswan-image-checks.json`; artifact upload
reported that no file was found and ignored it. This did not fail build 501,
so this run has no dedicated archived StrongSwan exclusion report. Commit
`be140259c6bf65663c378408dd104f60c3009923` adds an explicit exclusion report
and makes a missing report fail the workflow. Build 502 for that commit is
still running at the time of this record; its image result is pending.

No router setting, service or firmware was changed as part of this CI run.
