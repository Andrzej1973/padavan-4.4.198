# Checked MCU firmware-load responses

Added final manifest-checked isolated layer for three Method1 boot controls:
restart-download, target-address/length and FW-start. Vendor command/EID and
success=0 enum declarations are validated before transformation. Exact header
status/envelope and sequence-bound existing locked completion replace log-only
callbacks for these selected messages. Retransmission disabled, wrapper shares
serialized control admission, errors retain closed/uncertain ownership. Both
FW-start callers stop before runtime-stage publication on a failed result.
ROM patch/scatter paths are not claimed as newly checked. No owner claim,
sequence quarantine or firmware epoch is reset; same-adapter reopen still due.
SDK protocol headers are reviewed inputs, not rewritten. Installed inventory
and parent-manifest digest bind the change. No ordinary callback installation.

Host ASan/UBSan passed actual extracted dispatcher status/envelope/EID and
repeat-completion cases, actual consumed-message wrapper serialization,
uncertainty/replay refusal, all four MCU sequence lifetime suites, ACK gap/
quarantine fixture, owned OFF and staged close compatibility. Full source
inventory matched final manifest; duplicate install refused. CI will run these
on the installed final candidate. New boot code is NOT target/runtime verified.
Temporary overlays, binaries and 9464-byte phase bytecode removed. Existing
13.9MB generated source input retained for unfinished target/reopen work.

Optional744/41868468440 succeeded on a1f7d6d. Independently checked artifact
13344009986 module hashes/MIPS identity and defined 784-byte owned-OFF function;
compact reports in WR1200JS-BUILD744. Standard745 and ABI659 succeeded on
4088744. Required optional746/41873749862 dispatched once and now succeeded.
Artifact13345753999 independently checked baseline/WSC/reload module hashes,
source revision and new close functions. Reload early-RX function is600 bytes,
radio-off856, data-exit792, AP-release1124. Baseline early-RX remains refusal8
under LOAD_FW_ONE_TIME. Compact evidence in WR1200JS-BUILD746. These results
cover 4088744 close order, NOT this newer boot-result change. Next publish one
coherent boot package, verify new standard, then queue exact-SHA optional.
No router operation; full IoT/port acceptance remains open.
