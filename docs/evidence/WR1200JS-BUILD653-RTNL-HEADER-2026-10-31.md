# Build653: retry-worker RTNL declaration dependency

Run41239115796 attempt1, SHA c6db6c2ad90d82bfa248201fbf0924c938a051f0, job124649118661. The isolated peer82 source merge passed, including the production cmm_info station-query bounds. Full MIPS Kbuild began and failed compiling mt76x3/ap/ap_apcli_inf.c at worker calls rtnl_lock (line239) and rtnl_unlock (line241), with -Werror=implicit-function-declaration. Original timestamp2026-10-31T20:46:59Z. This is target compilation evidence of a missing dependency, not a successful module or device test.

Pinned c25283e kernel include/linux/rtnetlink.h declares both functions at lines27/28. The scheduler generator now adds this kernel header directly after rt_config.h in the translation unit defining the retry worker. The source audit requires one such include before that worker. No handwritten prototypes, relaxed compiler flags or worker/lifetime logic changes.

Executed checks: regenerated the final stage from its exact hash-pinned predecessor; compared all candidate files with the prior final stage. Only ap/ap_apcli_inf.c changes, exactly by the one include. Positive merged-source audit passed. Removing the include from scratch made the audit reject the actual failure condition; source restored. Initial negative test removal assumed LF at the header and was corrected to remove the marker independently of preserved CRLF; final negative check passed. Python AST and git diff --check passed. Scratch /tmp/wr-iot653-rtnl-wum1gynm. Full-chain replay and MIPS Kbuild of this revision remain CI gates.

Monitor run41240594336 identified the correct build/job/step but its old default-branch first256KiB excerpt omitted the late compiler diagnostics. Existing branch tail-log correction and late-error regression remain undeployed on trusted main; no duplicate parser change made. Source logs were treated as untrusted data. Raw original log and monitor artifact remain in private Windows staging.

No production installation, router writes, service restart or reboot. Next: publish one coherent repair and run the existing isolated peer82 target check on the exact new revision without duplicate active firmware runs.
