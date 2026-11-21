# Runtime closure composition and explicit selector linkage

## Actual retained backend composition

`check-runtime-edit-backend.py` joins the new revision lease, mailbox, edit
facade and the existing RC backend, activation owner, runner and normal OFF.
It turns profile A ON, replaces only the separate desired record with profile B,
then turns IoT OFF using a fresh B revision. The loaded A request remains intact
until its own OFF owner completes. There is one CLOSE/progress/release and no
desired SET or Save invocation. Failed isolation retains all three guards;
an actual process SIGTERM received during that wait routes after terminal
cleanup without duplicate CLOSE or premature signal replay. The final loaded
request is wiped and desired B remains unchanged.

This is a host composition proof. Driver, network, guard and normal-consumer
boundaries are actors. It does not prove RF completion, firmware ACK delivery,
physical PCI/DMA/IRQ quiescence or router acceptance.

## Selector evidence gap

Independent optional1382 audit at746ea2cc passed image CRC/SHA256, selected
embedded MIPS replacements, Classic assets and dependency closure. Its selector
object has a strong T definition, but the final stripped RC's dynamic symbol
table does not expose that function name. That absence alone does not establish
a linker bug, a wrong provider or successful execution. The old artifact lacks
the map/relocation evidence needed for a stronger independent conclusion.
Its durable audit explicitly retains this limitation.

The paired runtime preparer now removes only the exact weak placeholder from
the isolated prepared Ralink source and requires the strong saved-config-store
definition. The source verifier checks the prepared binding. The unpaired
baseline is untouched; the strong selector's existing proven-absence/factory
policy and native snapshot guard remain unchanged.

The isolated RC target appends a target-specific linker map/cref option while
preserving ordinary linker flags and libraries. CI retains that map, the strong
object symbol listing and the caller's relocation disassembly. The verifier
requires a strong saved-store provider, an actual Ralink selector relocation
and the map's saved-store definition/Ralink reference. It binds the report to
the final RC SHA256. Pairing reparses the raw evidence and compares the full
report, rather than trusting a true JSON flag or an exported dynsym name.

## Verification and pending gates

Native executed weak/strong override and stripped-ELF fixtures passed using a
real GNU linker map and relocation output. Source binding is checked against
the producer's literal C, with drift/duplicate rejection. Pairing and isolated
ROMFS staging negative fixtures passed. SDK runtime preparation passed after
the minimal fixtures supplied the actual producer prerequisite. The full
combined suite completed with exit0 before publication; shell syntax and
whitespace checks also passed.

MIPS target confirmation of the new explicit binding/map gate remains required.
No old image is retroactively declared to pass this new gate. Main-image
promotion, original ACK investigation, physical acceptance and four final
variants remain outstanding. This package changes build/source linkage and
verification only; it does not change driver queues, radio timing or firmware
protocol.
