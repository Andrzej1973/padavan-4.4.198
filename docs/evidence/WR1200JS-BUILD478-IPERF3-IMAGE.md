# WR1200JS build 478 — iPerf3 image evidence

GitHub Actions [run 39139346947](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39139346947)
completed successfully for project commit
`d1dc0ebaf82af316ad8ba65a01952c229c69e919`.

The build job ran `overlay/padavan-4.4/ports/iperf3/verify-image.py` against
the assembled `padavan-4.4/trunk` tree. The job log reports:

> iPerf3 status UI, HTTP handler and EN/UK/RU labels found in ROMFS; client test remains unverified

The resulting `iperf3-image-checks` artifact (ID `12140958985`) was uploaded.
The verifier source checks the effective selector, status UI/request code,
hidden-page refresh behavior, observation expiry, linked HTTP handler and
translations. This is image-packaging evidence for build 478 only.

The same-day read-only router sample records `iperf3_enable=0` and no process.
The sample could not identify the installed build from NVRAM, so it is not
runtime acceptance of build 478. No test client, throughput result, bounded
diagnostic session or start/stop behavior was verified on the device.
