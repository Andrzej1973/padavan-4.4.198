# WR1200JS service state checks #247

GitHub Actions [run #247](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39465292218)
completed successfully on 2026-10-20 against source SHA
`35d70beaba42bb4ef6aad57ad337cb3d1ff58823`. The single `lifecycle` job
completed successfully.

## Relevant service/WebUI checks reported by the job log

- SSH, iPerf3 and Privoxy process observations: stale observation expiry,
  stale-timer rejection, visible-page age checks and invalid-state refusal.
- Cron: bounded UI observation refresh/expiry and backend configured/observed
  states, including missing provider and observation errors.
- LLTD, ASUS Info Discovery, KMS and watchdog: bounded observations,
  refresh/expiry, and a shared `/proc` scanner that fails closed on read,
  enumeration and process-name errors.
- VPN profiles: create/edit/status/service paths, profile-specific storage and
  locks, endpoint/address/route/DNS validation, mocked link lifecycle, protected
  subnet refusal, and no-secret/no-auto-activation behavior.
- USB/IP: LAN/loopback policy, owned hooks, lifecycle and stop-timeout guards,
  candidate preflight, and device-action ownership/binding checks.

## Evidence limits

This is a source-level automated check run for commit `35d70be`, not a firmware
build or final-ROMFS audit. VPN network and USB/IP device operations use mocks;
the run does not establish that services start correctly on the router, that
the browser controls work against a live httpd, or that state persists across
reboot. It also predates the current uncommitted VPN selector correction and
does not validate that correction. Build #505 on the same commit failed earlier
in its pre-compilation VPN-pruning step; see
[`WR1200JS-BUILD505-FAILURE.md`](WR1200JS-BUILD505-FAILURE.md).
