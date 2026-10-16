# ZeroTier 1.16.2 on WR1200JS

Upstream: https://github.com/zerotier/ZeroTierOne at `fe29cd88886e4f58547ba7f740b2d73eb49ab222`.

## Verified compilation

[Run 37154558057](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37154558057) succeeded, including target source compilation. The candidate is ELF32, little endian, MIPS32r2/o32. Its artifact ZIP SHA256 is `2bc3e33f632c445de82358d7e4b3fe6c59beb168333d23e9f3bc594a36e8d5bc`.

The source recipe replaces the inherited prebuilt ZeroTier 1.14.0. It uses C++17, -O2, embedded client mode, static libstdc++, bundled miniupnpc/NAT-PMP, and the target libatomic. SSO, the nonfree controller and OpenTelemetry exporters are disabled. This is the client package, with CLI and identity tools.

Preparation preserves the rounding feature through the uClibc C function, fixes OpenTelemetry header paths, forces bundled NAT-PMP for cross-compilation and accounts for source-route attributes in netlink messages. It does not remove the TAP MAC-setting ioctl.

## Production image integration evidence

Update 2026-10-16: full build 315 at 78efe0d succeeded. The downloaded
ZeroTier image report passes all seven checks, including source-built code,
dependencies, lifecycle, WebUI and persistence assets. See
`evidence/WR1200JS-BUILD315.md`. Runtime remains unverified, and build 315
predates the newer status-semantics correction. The paragraphs below describe
the gates and historical integration work, not a claim of runtime acceptance.

The new recipe packages the target `libatomic.so.1`, which the base libc recipe does not install. An image gate checks the pinned source version, compares executable code with the source-built binary, checks target ELF format and recursively resolves shared-library and loader dependencies within ROMFS. CLI and identity-tool symlinks must resolve to the daemon.

A passing candidate compile does not prove the final image or router operation. The production image build, size, startup, network authorization and two-node connectivity still require evidence.

Existing service defaults remain disabled. Initial lifecycle hardening preserves identity and membership on stop. Additional join/leave controls, separate router/LAN permissions, bounded background refresh and complete status reporting remain in progress; do not claim that the full WebUI/lifecycle requirement is complete.

The pinned source is preserved locally. Downloading the upstream Git revision remains a dependency until the owned source mirror and complete backup are delivered.

## Status refresh contract — 2026-10-16

The newer adca670 change refreshes both the summary and the node/network cache
text through one authenticated JSON request. The HTTP hook reads at most 4096
bytes from an open cache snapshot and uses that snapshot's metadata for age;
it does not execute ZeroTier CLI in HTTP. Quotes, backslashes and line breaks
are JSON-escaped; the browser inserts the returned text using text(), not HTML.
An invalid response or transport failure clears previous details.

State 0 reflects the disabled configuration. State 1 means a cache no older
than 60 seconds and is labelled Updated, not Running. State 2 is stale data;
state 3 is unavailable/unknown. A future timestamp, invalid clock or irregular
file cannot establish freshness. None of these states proves controller
authorization, a healthy daemon, routes or two-node connectivity.

In [run 38841465981](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38841465981)
the pre-compilation status semantics step succeeded at adca670. It executes
the generated JS with transport mocks and the actual generated C hook compiled
with GCC, then independently parses its output as JSON. Escaping, fresh/stale,
future/missing/disabled states and truncation at 4096 bytes passed. This native
fixture does not replace full MIPS compilation or physical router acceptance;
the full run was still active when recorded.
