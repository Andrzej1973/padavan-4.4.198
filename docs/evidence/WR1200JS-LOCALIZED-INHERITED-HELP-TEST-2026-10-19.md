# WR1200JS inherited UI help localization test — 2026-10-19

Added `tools/check-inherited-dict-localization.py` as a pre-compilation test
for the inherited EN/UK/RU dictionary transform. It invokes the same pure
in-memory transform and final-image dictionary verifier used by production.
The fixture exercises untranslated-key insertion, stale Ukrainian/Russian
help replacement, retention of English-language coverage, and the image gate for inherited
labels and contextual help. It also rejects a changed source anchor, a
duplicate key, and a missing locale in final image dictionaries.

The first run exposed a real transform defect: updating an existing localized
help value replaced the entire `key=value` line with the value alone. The
transform now retains the key while replacing the value; the regression test
covers both existing and missing localized help entries.

The test is wired into `.github/workflows/build-padavan-4.4-wr1200js.yml` and
its path is included in the main build workflow's push filter. Local fixture,
`py_compile`, command-line help and `git diff --check` passed. The test no
longer creates temporary directories, so it runs on this Windows host as well
as Linux CI. An earlier filesystem-based fixture attempt left
`wr-dict-localization-m_w88xxr` with an access-denied ACL; cleanup of that exact
workspace-local directory was attempted and denied by Windows. CI execution
remains pending.

Follow-up: that exact locked directory was subsequently removed. The workspace
cleanup also removed other verified temporary leftovers. The in-memory test
does not recreate them.

Testing the real `EN.footer`, `UK.dict` and `RU.dict` directly from the verified
local Git archive of pinned source `c25283e915a2a00a763774dd255b14aff997285e`
found another mismatch: the IPv6 DNS help source uses `ZVMODELVZ`, while the
uncommitted transform expected `WR1200JS`. The source anchor is now checked
against its original placeholder, then the output uses board-neutral wording
in all three languages, avoiding a model-substitution mismatch in final ROMFS.
The changed-anchor negative fixture now operates on the original untranslated
input and asserts the exact expected failure; previously rerunning the
non-idempotent transform on translated input could fail at an unrelated earlier
anchor and give a misleading pass. Duplicate source locale keys and preservation
of an unrelated similarly named key are also exercised.

The same pinned archive's `trunk/user/rc/services_ex.c` writes `proxy-dnssec`
for `dhcp_proxy_dnssec=1`, with an explicit comment about forwarding upstream
validation results. EN/UK/RU help now describes that behavior and does not
promise local DNSSEC signature validation. No DNS configuration was changed.
LDPC help now uses a conservative description of error-correcting coding and
radio/driver/client support instead of propagating the inherited PMF requirement
claim. Capability exposure and radio settings are not changed by this wording.

The in-memory fixture, real pinned dictionary transformation/image-value
verification, Python AST parsing and diff checks pass locally. At verification,
PR head `132de67` was still building and did not contain this batch; a later
head must pass source preparation, final-image and browser checks separately.

This is a transform regression test, not evidence that the new strings are in
a firmware image or display correctly in a browser. Final-ROMFS verification
and Ukrainian/Russian browser review remain pending. No router setting or
firmware was changed.

Subsequent build #490 passed source preparation, the precompile dictionary
regression and the final-ROMFS dictionary verifier for head `8e3a681`.
This supersedes the pending-image status above; Ukrainian/Russian browser
display acceptance remains open. See
[build evidence](WR1200JS-BUILD490-SERVICE-AUDIT.md).
