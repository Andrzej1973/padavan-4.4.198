# Owned MIPS toolchains

All five MIPS workflow download paths use assets in our repository:
https://github.com/Andrzej1973/padavan-4.4.198/releases/tag/build-toolchains-v1

WR1200JS, Band Steering ABI, Zapret2 and Mi Mini use the original 28,358,192-byte
toolchain with SHA256 de412846a5d057faf132b2463aa29c24f77c79c744f4181c1a287bbeaf1d7256.
The upstream K2P control workflow retains its separate 13,925,308-byte compiler
archive (control suffix), SHA256
928db92fb2dd2d9f7cc540a40cbadaa2224b582e7b186f46c743d458ad768dc6.
The archives were copied unchanged; no compiler upgrade is implied.

Workflows use the fixed owned GitHub release-asset API endpoints, avoiding the
upstream release redirects that produced HTTP504. A shared Actions archive cache
is keyed by OS and hash; restored bytes are hashed before reuse. Downloads use
a partial file and are accepted only after SHA256 verification. No foreign
fallback exists. Cache misses may download from our release again; caches are
not guaranteed permanent. The owned release preserves the durable source.

sources.lock.json retains original URLs as provenance, records our release/API
locations and both archive hashes. The release includes SHA256SUMS and source
attribution. Existing component license/source inventory remains pending; no
new licensing claim is made. Do not replace assets silently: a compiler update
requires a new versioned release, digest and verification.

The normal workflow and optional ancestor verification share the reusable
workflow. New regression checks are required only when the checked-out source
contains their corresponding feature, so old revisions do not run missing files.
check-owned-toolchains.py executes the actual five download blocks offline for
cache hit/miss/corruption, network failure and wrong-hash refusal. This is not a
firmware or device acceptance test. Independent original/owned round-trip evidence
is in evidence/WR1200JS-OWNED-TOOLCHAINS-2026-11-08.json.
