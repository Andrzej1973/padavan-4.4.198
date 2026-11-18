# Revision-bound Classic runtime ON/OFF

## Behavior and call chain

The candidate Classic page now separates saving desired configuration from
turning the captured saved profile ON/OFF now. Runtime buttons use the public
view captured on the last explicit read, not unsaved form edits. No password is
returned to or submitted by the browser for these actions. An absent configured
record leaves both runtime buttons disabled. Factory OFF and no-auto-submit
behavior remain unchanged.

`classic-config.js` → authenticated POST `wr_iot_edit_runtime.cgi` → actual strict
form parser with endpoint-owned RUNTIME mode and mandatory KEEP → typed client
and mailbox → same RC revision lease/pin and native-current comparison →
`wr_iot_config_runtime_request()` → existing `wr_iot_activation_execute()` and
continuation → existing backend applied-route gate → terminal publication and
private current-state observer.

The new edit mode is a distinct operation. The existing RAM/AUTO/explicit record
encodings keep their values and representation. A runtime edit cannot REPLACE a
key, return STORED_RAM/SAVED_FLASH, call the config/Save owner or claim success
from queue acceptance. Older decoders refuse the new `runtime` mode. Paired
candidate packaging is still required; this is not permission to mix binaries.

RC resolves the key privately against the exact current lease. Canonical
comparison permits only the requested enabled bit to differ from the captured
profile; changed SSID/key/subnet refuses before activation. ON delegates the
complete resolved profile; OFF delegates the existing empty runtime envelope,
so the retained active owner supplies its own close identity. Desired settings
are not rewritten or committed by this action. Configuration-save paths remain
separate. The existing per-BSS backend checks the actually loaded key/ownership;
a mismatch does not trigger physical restart or automatic scan.

Execution remains once-only. A pending operation retains its lease/admission,
and unknown results are not replayed. APPLIED requires the existing normal
shutdown/ownership route gate; failed terminal publication/readiness retries
do not rerun activation. The RC status endpoint observes completed edit-runtime
receipts through the edit facade and existing backend current-state checks.
No driver, MCU ACK, descriptor release, PCI/DMA/IRQ, radio timing or firmware
protocol is modified by this package.

## Candidate packaging and verification

Source metadata now requires `http_runtime_toggle_bound` alongside exact
authenticated route preparation. Both Classic preparers and the pair verifier
refuse missing or false metadata. `activation_control` now truthfully reports
true for the candidate page. Production and runtime-acceptance flags remain
false; ordinary standard firmware still excludes the candidate.

Checks passed before publication:

- Complete focused edit/view suite with strict C/ASan/UBSan, actual native-source
  preparation, Classic source staging and DOM fixtures.
- Sixteen actual parser/client/mailbox/RC/lease/owner composition scenarios,
  including ON/OFF with no native SET/COMMIT, altered SSID/range and expired
  lease refusal, retained applied-route wait without repeat execution, and
  wrong RAM/flash results remaining RECOVERY. Activation/flash/SDK are actors.
- Pure canonical conversion and codec checks; runtime replacement keys refuse.
- Real Windows Edge DOM: three save modes, both runtime buttons, captured-view
  selection despite unsaved edits, secret clearing, unknown no-replay, expired
  view and clock regression refusal. AJAX and frame are fixtures; all page
  network requests are blocked. Temporary browser profile removed.
- Existing RC wait/status observer and candidate manifest/staging checks.

Full SDK source preparation also passed, including the actual staged headers
and object mappings. Exact-source MIPS link,
candidate TRX/embedded assets and independently authorized device acceptance
are still required. This does not complete loaded-profile reprovisioning UI,
main-image promotion, four final variants, original ACK investigation or
physical acceptance. Do not label IoT or the firmware complete from these host
results. Browser details and exact asset hashes are in the companion Edge report.
