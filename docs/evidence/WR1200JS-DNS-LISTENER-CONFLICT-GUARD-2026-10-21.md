# WR1200JS Stubby/DoH listener-conflict guard evidence

Date: 2026-10-21
Scope: source and host-shell checks for the selected Stubby/DoH service pair.
This report does not claim final-image, target BusyBox, or router acceptance.

## Change under review

Added a common bind-address/port conflict guard used by both service start
paths. It checks the other service's enable flag and packaged executable,
compares the listener address (including IPv4 wildcard binds), and accounts
for each configured DoH resolver's `base_port + slot` listener. It now fails
closed when an enabled packaged peer has an invalid bind mode or port, since
the guard cannot safely prove the listeners are disjoint. It runs only while
starting/configuring a service, so the stop paths do not depend on the guard
being present. Each package installs its own copy at a distinct ROMFS path;
both image verifiers check that the installed copy matches its prepared source.

The Stubby form already specified ports 1024..65535 while the startup script
and dnsmasq emitter accepted 1..65535. Both now enforce the form's range; the
guard also rejects an enabled Stubby peer on a system port. The dnsmasq emitter
keeps `no-resolv` when rejecting an invalid listener, preserving the existing
strict-mode behavior and NTP-only bootstrap exceptions. Stored settings are
not rewritten by this change. The image runner's DoH guard source path was
corrected from the nonexistent `ports/doh/dns-listener-guard.sh` to the shared
`ports/dns-common/dns-listener-guard.sh`.

## Checks performed

- The host fixture
  `overlay/padavan-4.4/ports/dns-common/check-listener-conflicts.sh` passed 17
  collision/non-collision and invalid-peer scenarios under Git for Windows `sh.exe`:
  same loopback bind rejected; stale enable flags without the other package's
  executable allowed; second DoH resolver offset collision rejected; equal
  ports on distinct specific addresses allowed; wildcard overlap rejected;
  default listener ranges allowed; disabled DoH ignored; and DoH-side checks
  agree with Stubby-side checks; invalid modes, malformed/out-of-range ports
  and a Stubby system port fail closed.
- Sandbox runs failed before shell startup with `couldn't create signal pipe,
  Win32 error 5`. The same local checks subsequently passed outside the sandbox.
  No Windows configuration or credentials were changed. WSL was not used.
- `check-stubby-config.sh` passed the actual configuration-generator fixture,
  including rejection of ports 53/1023, acceptance of 1024/65535 and retention
  of the previous configuration on all rejected inputs. `sh -n` passed for all
  seven relevant shell files.
- The combined-emitter checker now executes on Windows with native GCC instead
  of unconditionally skipping execution. All ten C scenarios passed using the
  actual emitter sources: four combined/individual mode cases and six Stubby
  port boundaries (0, 53, 1023, 1024, 65535, 65536). Compilation used
  `-Wall -Wextra -Werror -O2`. Its first full compilation exposed a truncation
  warning in both IPv4 bootstrap copies; the copies now explicitly bound the
  already validated IPv4 string to 15 characters, and the rerun passed.
- Python AST parsing passed for both package integrators, both image verifiers,
  and the existing combined-dnsmasq checker.
- Eight structural assertions passed: start-path ordering, package ROMFS
  installation, both source-copy integrations, workflow host gate, target
  QEMU fixture wiring, and both image-verifier source-identity checks.
- `git diff --check` passed. Git printed CRLF-to-LF notices for modified
  documentation; no whitespace error was reported.

## CI and runtime status

### Build #513 follow-up — 2026-10-21 16:57 UTC

GitHub Actions run [#513](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39632923432)
used PR head `8ff6016947bcb19363a7f0ddbc502a217432868b`; its job checked out
the PR merge commit `7160ecdb267c6c974590c57a63abeef27f5998ec`. The log shows
the DNS listener-conflict scenario check passed, the combined DoT/DoH dnsmasq
configuration was accepted by the built target dnsmasq under QEMU, the image
Stubby lookup step passed, and the exact target BusyBox shell audit passed.
These results verify the exercised guard/configuration and selected image
checks for that run, not live DNS behavior on the router.

The run later failed at the Privoxy final-image gate. Consequently subsequent
DoH packaging, discovery/KMS image checks and other gated steps were skipped;
this run does not prove that DoH was packaged. It also produced no verified
downloadable image. DoH image verification, simultaneous live DoT/DoH behavior,
upstream preference/failover, persistence and router runtime remain open.

This supersedes the earlier statement below that no CI result included the DNS
listener guard. The later #513 workflow did exercise its host/target checks,
although the overall image verification did not complete.

Historical note from the original report: at that checkpoint, the workflow's
host fixture was wired but the target BusyBox/QEMU and image-verifier checks
had not yet run. This was superseded by the #513 results above for the checks
that actually ran. DoH image verification still did not run because the earlier
Privoxy gate failed.

At the time the local source patch was prepared, no firmware build was started.
Later, #513 built the firmware and completed the DNS checks recorded above,
then failed the Privoxy gate. No router setting/service was changed, and no
router reboot or flash was performed. DoT/DoH live DNS behavior, failover,
restart behavior, persistence, and simultaneous service operation remain
unverified on the physical WR1200JS.
