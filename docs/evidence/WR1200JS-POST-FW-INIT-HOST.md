# Post-firmware ASIC initialization failure policy — 2026-11-06

The SDK NICInitializeAdapter normally continues after PDMA-idle timeout unless
NIC_NOT_EXIST is set, and may reload firmware once after ASIC init failure.
Those paths are inappropriate for a bootstrap with a committed firmware
receipt and frozen constructors: continuing after failed idle observation or
implicitly reloading invalidates the checked initialization sequence.

The isolated post-fw-init layer captures the bootstrap ticket on entry. For
bootstrap it attempts historical loader-abort and returns failure immediately
on either idle timeout or ASIC init failure, without firmware retry. Ordinary
behavior keeps its bounded one-reload policy, but a failed NICLoadFirmware now
returns failure instead of entering another ASIC attempt with failed loading.

Generated NICInitializeAdapter host execution passed ASan/UBSan with feature
guards on/off: owned/ordinary, NIC present/removed, idle failure, ASIC failure,
reload failure, captured-ticket provenance across ASIC-side epoch mutation,
bounded ordinary retry and no bootstrap firmware reload. Abort is injected
and deliberately returns failure: attempting it is not proof that DMA stopped.
MCUSysInit routing and command-admission fixtures also pass. Fresh complete
inventory matches the manifest; outer bootstrap-init refusal remains present.
Temporary candidate (~14MB) and executables were automatically removed.

The CI peer82 recipe stages the layer/test; no target proof yet. Normal startup
configuration admission, data promotion and its error cleanup remain unfinished.
In particular the future caller must preserve resources when abort cannot prove
DMA stop; this local failure return does not validate generic err8 cleanup.
The current outer gate still prevents reaching this post-firmware bootstrap
path in production. No normal admission or runtime acceptance is claimed.
