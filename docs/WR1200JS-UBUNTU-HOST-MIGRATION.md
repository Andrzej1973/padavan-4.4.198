## Owner priority: IoT on Ubuntu22.04 — 2026-11-11

Continue WR1200JS IoT development and acceptance work on Ubuntu22.04, which
remains the default build host. Ubuntu24.04 is a deferred candidate: its current
runs may finish, but host comparison must not block or displace IoT. Switch the
default only after the required24.04 standard/optional checks pass and their
artifacts are verified. Do not add libcurl-only investigative builds. Modern
WebUI remains paused. Router changes still require separate direct approval.

## Owner steering after the initial comparison

The owner deferred further libcurl root-cause investigation: wait for optional
results and then decide host adoption. Do not require additional diagnostic
builds solely to explain internal symbol exports. Generated-flag collection
remains an unpublished draft, not an enabled migration requirement.

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

## Selective DNS evidence and mirror failover

Run1013 artifact13868188054 confirms all three Ubuntu names time out through
NSS and curl, while GitHub and Microsoft NSS/HTTPS succeed; no proxy variables
were present. This narrows the failure to a selective resolution problem; it
does not identify whether upstream DNS filtering, cache or authoritative DNS
is responsible. No resolver modification is justified by this evidence alone.

The second bounded apt attempt now selects https://mirrors.xtom.com/ubuntu
for all four pockets including security. xTom appears in Ubuntu's registered
archive mirror list: https://launchpad.net/ubuntu/+archivemirrors . Local HTTPS
probes returned200 for noble/InRelease and jammy-security/InRelease; actual
runner reachability and package installation remain unverified until CI.
Ubuntu archive signature/hash validation and TLS remain enabled, strict update
rejects incomplete or expired metadata, and mirror unavailability still fails
closed. This preserves distro/package selection; it does not promote the host.
Offline executable fixtures cover primary success, fallback after primary
failure, final failure and inclusion of the security pocket.

## Build1014 exposed a second apt path

Ubuntu22 firmware build succeeded, but Stubby QEMU gate failed before test
execution: a late raw apt invocation could not locate qemu-user-static. It used
the runner default sources rather than the temporary source selection used by
the successful initial install. QEMU/dnsutils/iptables/proot now belong to the
initial bounded dependency transaction; later runtime gates perform no apt.
An offline regression rejects late raw apt calls and verifies those packages
are included. Monitor report identified the step but omitted the actionable
package error; a minimal matcher and dedup fixture cover that omission.
Neither QEMU nor device runtime acceptance is implied by compilation success.

Ubuntu24 run1015 reached ntfs-3g autoreconf and failed on missing
AM_PATH_LIBGCRYPT (configure.ac337); AC_MSG_ERROR/WARN diagnostics follow that
missing expansion. libgcrypt20-dev explicitly supplies the host aclocal macro
/usr/share/aclocal/libgcrypt.m4 according to Ubuntu's Noble package file list:
https://packages.ubuntu.com/noble/amd64/libgcrypt20-dev/filelist . Added as a host
build dependency on both control and candidate; target toolchain unchanged.
Monitor43053290766 already retained the causal diagnostic; no parser change
needed for1015. Full target build verification of this correction is pending.

## Standard image comparison at4f80200

1016 Ubuntu22 and1017 Ubuntu24 passed standard; exact source/toolchain selection
matches. Independently verified uImage CRC/length/product/partition and embedded
HNAT policy for both actual artifact images. Full firmware/kernel configs match.
Both SquashFS inventories contain1534 regular/symlink records and identical paths;
17 byte differences, including three dictionary build timestamps. Ubuntu24 TRX
is17096B smaller. Full evidence is recorded in
`evidence/WR1200JS-UBUNTU-STANDARD1016-1017-2026-11-11.json` and
`evidence/WR1200JS-UBUNTU-STANDARD-CONTENT-2026-11-11.json`.

libcurl has763 fewer defined dynamic exports on24, but all100 curl_-prefixed
exports match; NEEDED/SONAME/interpreter/MIPS flags match. No undefined imports
of removed names were found across287 Ubuntu24 image ELFs. This excludes neither
external plugins nor dlsym lookup and does not establish identical behavior.
Both logs accept -fvisibility=hidden; staged HTTP dependencies selected correctly.
The quiet library builds do not expose enough actual compile/link flags to
explain visibility differences; capture generated CMake/libtool flag provenance
in the next coherent CI verification before claiming a root cause. Keep22 default.

Optional1018/43058250743 (22) and1019/43058278935 (24) verify exact4f80200/iot/peer82;
dispatched only after both standard successes, with no matching optional active.
Their target/feature results and device acceptance are still pending.
