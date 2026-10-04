# Candidate rc profile integration

prepare-profile-integration.py connects the read-only compatibility policy to the actual rc/ralink.c profile generator behind CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y. Hardware compilation is restricted to USE_WID_2G=7603 and USE_WID_5G=7612. Missing/default wr_bs_enable is off. Enabled profiles require matching valid main credentials; mismatch remains off without changing credentials. Modern BndStrgBssIdx explicitly selects only the main BSS and writes zero for every guest BSS.

The rc Makefile receives the policy object only under the candidate build selector. Normal firmware does not yet run this preparer or select that option. Isolated CI extracts the actual helper and exercises its output against mocked NVRAM, host sanitizers and MIPS compilation. This is not full rc compilation or actual radio operation.

Activation integration must serialize settings changes, exclude competing daemons, coordinate driver reinitialization and listener/daemon startup, and await driver acknowledgements. The runtime switch must remain factory-off; first activation may disconnect participating clients. Service, UI and runtime acceptance remain pending.

## Full candidate build failures, 2026-10-04

Run 37194364331 completed with the baseline firmware build and image checks passing, but isolated full drivers and rc linking failing. The legacy admission macro dereferenced a literal NULL (void pointer); it now evaluates its argument once into a typed wifi_dev pointer before the main-BSS guard. The fixture now exercises the actual literal-NULL call shape. This preserves the existing no-device admission semantics; authenticating call sites using NULL still require a separate review before steering can be called complete. The rc integration added its object before the base OBJS assignment, which overwrote it. The gated object registration is now after the base object list. Full rebuild verification is pending; neither correction enables production steering or WPS.

Control workflow 37194680571 completed successfully. This proves the isolated workflow checks and compilation, not live radio interoperation or production service integration.
