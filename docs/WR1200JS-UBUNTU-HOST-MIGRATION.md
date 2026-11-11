# WR1200JS Ubuntu host candidate — 2026-11-11

Owner authorized this parallel workstream while IoT work continues. Modern WebUI
remains paused. Local WSL stays Ubuntu 22.04. No router operations are authorized.

## Controlled comparison

The existing firmware dispatcher now accepts `build_host`: `ubuntu-22.04`
(default/control) or `ubuntu-24.04` (manual candidate). Both use the same
`source` owned Release toolchain, source revision, WR1200JS configuration and
image gates. This does not rebuild or update the toolchain. Run standard first,
then optional with `candidate_scope=iot`, `iot_candidate_variant=peer82` for the
same SHA. Existing exact ancestor selection is still optional-only. Candidate
host queues append `-ubuntu24` to the normal lane group; default lane group names
and cancellation policy are preserved. Host-built compiler caches use host-specific
v4 keys; immutable checksum-verified toolchain and source archives remain shared.
Workflow title and `/etc/os-release` record the selected host. No automatic
promotion to Ubuntu 24.04 is implemented.

Acceptance requires successful standard firmware/image gates and optional IoT
driver compilation on both hosts for matching source/toolchain/configuration.
Compare ABI dependencies, image manifest, size and build duration; image hashes
need not be identical (build identity/timestamps). Only then choose the default
host. Build verification is distinct from deferred physical router acceptance.

## Evidence and upstream review

nilabsent/padavan-ng README explicitly documents Ubuntu 24.04 dependencies:
https://github.com/nilabsent/padavan-ng/blob/c29b12da69b1593a6e8cf65cd43767fc99bb6386/README.md
Compared locked donor d2c5846299949c57a4e867284069900b561dd2a4 with that HEAD:
30 commits ahead, no files under toolchain/ changed. Changes include nfqws2
1.0.6, Tor 0.4.9.15, certificate and ipset/WireGuard/Zapret updates. These are
separate package-review candidates, not bundled into this host migration.

1009 was cancelled after prolonged apt DNS errors. Replacement1010
(43044376432, source099b4bb0e8aac6ddd1b3433d39dca4871208fb6d) failed in dependency
installation before firmware compilation. Monitor43045561471 artifact13865614745
correctly identified the failed run/job/step but omitted the causal DNS text.
Original job130604550400 confirms repeated `Temporary failure resolving
'azure.archive.ubuntu.com'`; Microsoft repository downloads succeeded. Evidence
supports an Ubuntu mirror resolution failure, not a compiler regression or
proof that all runner DNS was unavailable. The previous bound limited failure
to six minutes but did not repair the mirror path.

Dependency installation now uses a temporary explicit official archive/security
source list for this apt invocation only, without runner mirror-list indirection
or saved apt/resolver changes. Uses libncurses-dev on both hosts, strict update,
180s update / 420s install bounds, two attempts, 22-minute step bound. DNS failure
can still occur and will fail closed. Monitor adds bounded DNS-line recognition
and a real-case fixture with dedup/success silence. Monitor executes trusted main
code, so branch-only parser changes are not deployed to that trusted code yet.
