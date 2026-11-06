# Isolated MCUSysInit scheduler routing — 2026-11-06

After successful NICLoadFirmware, the isolated MT7603 PCI bootstrap route now
calls wr_iot_mcu_boot_scheduler_run with a ticket copied before loading. It
returns success only for NDIS_STATUS_SUCCESS and avoids the ordinary SDK call.
Loader or scheduler failure attempts the historical loader-abort with the same
captured ticket and returns failure. Abort refuses stale/already consumed
ownership; this routing does not authorize resource release on uncertainty.

The ordinary HIF_MT route now tests SDK TRUE explicitly and returns failure for
FALSE instead of silently reporting the successful loader result. USB and
non-MT guards retain their applicable paths. No new normal admission is granted.

Fresh generation and actual generated MCUSysInit host execution passed
ASan/UBSan with feature guards disabled, MT/USB, and MT7603/PCI. Injected loader,
scheduler and abort operations exercise loader failure, scheduler failure,
captured-ticket identity across loader-side epoch mutation, no double SDK call,
ordinary TRUE/FALSE normalization, FwInit selection and call order. The complete
generated inventory matches its manifest. The outer rtmp_init_inf bootstrap
refusal was explicitly checked present. Temporary candidate (~14MB) and test
executables were automatically removed.

This fixture checks MCUSysInit routing with subordinate operations injected;
it is not an end-to-end hardware or connected-loader proof. The peer82 recipe
stages the layer and fixture; target compilation is pending. All-producer
exclusion, startup configuration command policy, normal sender/data promotion
and repeated lifecycle acceptance remain outstanding. Do not remove the outer
gate or execute this candidate on a device based on this source/host result.
