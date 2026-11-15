# Cold/IoT-OFF and concurrent physical admission audit

The never-opened ra2 path differs from an owned CLOSED ra2:

- `initial-off.c:wr_iot_initial_off_begin/observed` uses fresh idle epoch,
  generation and increasing observation serial, no OPEN token or CLOSE serial.
- `prepare-restart-entry-source.py` keeps IDLE/INITIAL_OFF on the separately
  guarded legacy SDK path. Claimed owned restart returns before that path.
- `rc-backend.c:wr_iot_activation_prepare_radio_stop` admits only fresh
  never-opened evidence there. Missing bridge/empty config alone is insufficient.
- `quiesce_begin` admits actual ACTIVE/OFF backend owners, not INITIAL_OFF.
  Physical STOP protocol requires nonzero OPEN/CLOSE provenance, so never-opened
  idle evidence cannot be converted into that RELEASE tuple.
- Current private ON root requires enabled1 and historical physical RELEASE;
  it does not yet restore Main/Guest with desired IoT OFF. Public physical OFF/ON
  binding stays disabled until that separate lifecycle is implemented. Existing
  cold-path source tests do not prove device acceptance.

The audit found a concurrent-admission hole: after ON parent release, signal
admission is inactive but the root still owns WAN/IAPP. Direct physical_begin
and restart_entry checked active/pending only. Both now refuse process-owned
ON/OFF exclusion before scheduler preparation, mode reads, fences or driver
work. This keeps the normal never-opened path available when no owner exists.
Focused actual physical/session/fence fixture verifies both flags cause zero
scheduler/guard/driver calls; entry fixture checks zero mode/guard/submission.
Normal OFF composition, ON shutdown, prepared entry and separate units pass.
Host checks use backend/SDK transports; target/device claims remain separate.

Next: define typed never-opened physical stop/resume provenance or explicitly
validated cold SDK routing, and a saved-IoT-OFF Main/Guest restoration path.
Do not invent OPEN token/close serial, convert idle to CLOSED, or globally loosen
physical admission. Keep ordinary precreated ra2 runtime toggle independent.

## Rechecked evidence boundaries

`check-initial-off-composition.py` and `check-initial-off-owner-composition.py`
were rerun against current source: the existing never-opened initial-OFF
observation/owner path passes host composition. This does not add a physical
OFF/ON lifecycle for desired IoT OFF.

Optional1257/43691352008 artifact14155452722 was independently inspected. Its
verification-source artifact identifies verified28229bf1 versus dispatch68a3e7f1.
Target result matches verified28229bf1 and reports compiled peer82 MT7603 module
SHA256 e2675b461ebb8712b1cff86892aac0ac55c757ce63581c1ad78ba976211bab64.
Actual RC/HTTPD ELF headers are MIPS32r2 and both dependency-closure reports pass
with no errors. The reports explicitly retain production_installed=false and
runtime_verified=false. This verifies that older candidate, not subsequent ON
root/shutdown patches or final image inclusion. Full JSON/hash evidence is kept
in WR1200JS-OPTIONAL1257-TARGET-LINK-2026-11-15.json. Archives were inspected in
memory; no extracted firmware/build tree was retained.
