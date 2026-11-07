# WR1200JS read-only SSH timeout — 2026-10-25

## Attempt

The repository's fixed read-only helper was invoked with its `identity` check:

```text
powershell -NoProfile -ExecutionPolicy Bypass ^
  -File .\tools\wr1200js-readonly.ps1 identity
```

Result: exit code `1`, with:

```text
ssh: connect to host 192.168.20.1 port 22: Connection timed out
```

The helper uses Windows OpenSSH, the configured owner key, batch mode,
identity-only authentication, a fixed remote command and normal SSH port 22.
No alternative executable, proxy bypass, security-setting change or arbitrary
remote command was used.

## Evidence boundary

No remote command was confirmed to execute. This observation says nothing about
the current router process table, generated firewall rules, current firmware
identity or tunnel health. It only shows that the configured management path
was unreachable from the current executor at that time.

Zapret2 device runtime remains unverified. The router was not flashed, rebooted
or reconfigured for this check.
