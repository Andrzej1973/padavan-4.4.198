# ZeroTier 1.16.2 on WR1200JS

Upstream: https://github.com/zerotier/ZeroTierOne at `fe29cd88886e4f58547ba7f740b2d73eb49ab222`.

## Verified compilation

[Run 37154558057](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37154558057) succeeded, including target source compilation. The candidate is ELF32, little endian, MIPS32r2/o32. Its artifact ZIP SHA256 is `2bc3e33f632c445de82358d7e4b3fe6c59beb168333d23e9f3bc594a36e8d5bc`.

The source recipe replaces the inherited prebuilt ZeroTier 1.14.0. It uses C++17, -O2, embedded client mode, static libstdc++, bundled miniupnpc/NAT-PMP, and the target libatomic. SSO, the nonfree controller and OpenTelemetry exporters are disabled. This is the client package, with CLI and identity tools.

Preparation preserves the rounding feature through the uClibc C function, fixes OpenTelemetry header paths, forces bundled NAT-PMP for cross-compilation and accounts for source-route attributes in netlink messages. It does not remove the TAP MAC-setting ioctl.

## Production image integration pending

The new recipe packages the target `libatomic.so.1`, which the base libc recipe does not install. An image gate checks the pinned source version, compares executable code with the source-built binary, checks target ELF format and recursively resolves shared-library and loader dependencies within ROMFS. CLI and identity-tool symlinks must resolve to the daemon.

A passing candidate compile does not prove the final image or router operation. The production image build, size, startup, network authorization and two-node connectivity still require evidence.

Existing service defaults remain disabled. Initial lifecycle hardening preserves identity and membership on stop. Additional join/leave controls, separate router/LAN permissions, bounded background refresh and complete status reporting remain in progress; do not claim that the full WebUI/lifecycle requirement is complete.

The pinned source is preserved locally. Downloading the upstream Git revision remains a dependency until the owned source mirror and complete backup are delivered.
