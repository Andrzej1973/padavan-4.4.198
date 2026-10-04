# Band Steering main-network isolation

Pinned base c25283e915a2a00a763774dd255b14aff997285e has a legacy MT76x2 admission macro accepting a wifi_dev argument but not using it. Its BndStrg_IsClientStay RSSI path also has no BSS check. Enabling these paths unchanged can therefore affect guest clients.

The candidate preparation requires exact original header and original or grant-prepared AP source hashes. It allows non-main/null-device admission without invoking steering admission, and returns TRUE before RSSI/table operations for guest/null-device clients. Existing main-network steering behavior and separately configured RSSI Kick controls are retained. The modern MT76x3 profile must explicitly select only the main BSS; service/profile integration remains pending.

Fixtures extract the actual prepared macro and RSSI function, exercise main/guest/null-device behavior, and compile for MIPS. Mock callbacks are not proof of router operation. The current full-driver run 37192024927 was started before this candidate and cannot prove its full-driver compilation. The candidate is not installed in production firmware.
