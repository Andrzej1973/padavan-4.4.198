# Candidate rc profile integration

prepare-profile-integration.py connects the read-only compatibility policy to the actual rc/ralink.c profile generator behind CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y. Hardware compilation is restricted to USE_WID_2G=7603 and USE_WID_5G=7612. Missing/default wr_bs_enable is off. Enabled profiles require matching valid main credentials; mismatch remains off without changing credentials. Modern BndStrgBssIdx explicitly selects only the main BSS and writes zero for every guest BSS.

The rc Makefile receives the policy object only under the candidate build selector. Normal firmware does not yet run this preparer or select that option. Isolated CI extracts the actual helper and exercises its output against mocked NVRAM, host sanitizers and MIPS compilation. This is not full rc compilation or actual radio operation.

Activation integration must serialize settings changes, exclude competing daemons, coordinate driver reinitialization and listener/daemon startup, and await driver acknowledgements. The runtime switch must remain factory-off; first activation may disconnect participating clients. Service, UI and runtime acceptance remain pending.

## Full candidate build failures, 2026-10-04

Run 37194364331 completed with the baseline firmware build and image checks passing, but isolated full drivers and rc linking failing. The legacy admission macro dereferenced a literal NULL (void pointer); it now evaluates its argument once into a typed wifi_dev pointer before the main-BSS guard. The fixture now exercises the actual literal-NULL call shape. This preserves the existing no-device admission semantics; authenticating call sites using NULL still require a separate review before steering can be called complete. The rc integration added its object before the base OBJS assignment, which overwrote it. The gated object registration is now after the base object list. Full rebuild verification is pending; neither correction enables production steering or WPS.

Control workflow 37194680571 completed successfully. This proves the isolated workflow checks and compilation, not live radio interoperation or production service integration.

### Authentication call and full-build trigger follow-up

Pinned mt76x2 ap_auth.c resolves apidx, validates it against BssidNum, and assigns wdev=&pMbss->wdev before the Band Steering call. The call previously passed NULL. The isolated preparation now passes that resolved wdev, allowing main-BSS admission checks while preserving guest bypass. The exact source SHA and call/assignment anchors are required before mutation; the source-check generator verifies the changed call. Local preparation of all three actual pinned files and fixture generation passed. Actual full driver compilation and device acceptance remain pending. Main-bss header after SHA 8b675ef7ef4a7a12eab043f04973970cf4f39763d52c992a0dd5ebdea8d5e3a7; ap_auth after SHA d1c8e36a7112b08c180f2171ce1f031c51840c02e82b2852919de1b0d331bab3.

ABI workflow 37195895557/job111417560275 at commit156492222 completed successfully after the typed-macro and rc object-registration corrections. It does not compile the entire drivers/rc. Add exact candidate preparer/policy/compiler-wrapper paths to the multi-board push trigger so changes exercised by its isolated full probes actually request a full build. No production selector is enabled by this trigger change.

## Candidate local Band Steering administration client

ctl.c provides only status and stop using the existing fixed local endpoint. Root-only operation, validated private directory/socket, kernel credentials on replies, connected datagrams, bounded response and two-second observation timeout. STOP success means request acknowledged, never proof that the driver is OFF; absent endpoint/timeout is unverified state. No driver commands, profile writes, service installation or WebUI integration occur here. Host and exact MIPS compilation are added to the isolated ABI workflow; real client/server integration and runtime router acceptance remain pending. Current full firmware run37196036035/job111418011054 remains live at dependencies; ABI run37196035781/job111417985628 completed success. Previous turn made authoritative source changes, so it counts as progress.
