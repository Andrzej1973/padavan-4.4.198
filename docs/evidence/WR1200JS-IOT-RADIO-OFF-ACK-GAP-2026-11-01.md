# Radio-off completion evidence gap

Reviewed candidate source based on c25283e915a2a00a763774dd255b14aff997285e.
`hw_ctrl/cmm_asic_mt.c` LOAD_FW_ONE_TIME branches set/clear AGG_TEMP upper16;
all driver-source AGG_TEMP references were inspected. No explicit firmware
completion event/poll for that operation was found in this tree. This is
absence of a source implementation, not proof that hardware cannot support it.

`mcu/andes_mt.c:1777` CmdRadioOnOffCtrl initializes an extended command with
EventExtCmdResult then returns AndesSendCmdMsg's result. The callback at1649
reads u4Status and logs/hooks it, but does not populate a caller-owned result
or validate Len itself. Thus its wrapper's success cannot by itself establish
firmware status success. Do not globally alter this shared callback: many
unrelated commands depend on it.

Required next work: trace cmd_msg response ownership and AndesSendCmdMsg's
wait/timeout semantics, then create a radio-off-specific bounded response
handler with length, command identity and firmware-status validation and
caller-lifetime proof. Confirm LOAD_FW_ONE_TIME compatibility separately;
a validated response parser does not authorize replacing its register policy.
Retain existing guard until actual completion protocol is supported. Rejected,
malformed, missing and late responses must remain failure/unknown, with no
unsafe stack response pointer or claimed DMA quiescence.

No radio command, register write, flash or reboot was performed.

## Correction after complete candidate trace

The generic callback analysis above is accurate only for the legacy wrapper.
The candidate ALREADY has an opt-in checked cmd_msg path: andes_mt.c1762
wr_iot_prepare_radio_off builds checked messages; andes_mt.c2958..2976
validates response identity, exact packet/payload length and firmware status
under ackq_lock, stores result in message-owned fields, then completes wait.
andes_core.c905..909 copies checked verdict before queue transfer/free and
keeps timeout failure separate from late-response fields. No stack result
pointer is used. Therefore do not implement a duplicate response mechanism.

At that historical checkpoint the checked hardware path still invoked legacy
CmdRadioOnOffCtrl and the checked builder was unused. This was subsequently
changed by the final-stage generator; see the current status below.

## Current wiring audit — resumed at 9555bcd

`tools/iot/prepare-aux-family-retry-scheduler.py` now injects
`wr_iot_send_radio_off_checked`, which rejects a null adapter, calls the existing
`wr_iot_prepare_radio_off`, rejects allocation failure and returns
`AndesSendCmdMsg`'s verdict. The generator redirects only the checked hardware
radio-off call to this wrapper; the generic CmdRadioOnOffCtrl stays unchanged.
This closes the previously documented unused-builder wiring gap. It does not
close firmware-policy or terminal-removal gaps.

`tools/iot/check-radio-off-send.py` exercises the extracted generated wrapper
with injected message ownership and checks null/allocation/send failure and
success. These host tests do not execute MCU transport, real callbacks or DMA.
Under LOAD_FW_ONE_TIME the checked hardware entry still returns FALSE before
mutation, so the default feature configuration cannot use this checked send
path as proof of physical radio shutdown. Keep the guard until a supported
completion protocol or independently justified loading policy is verified.

Terminal PCI remove also retains early returns before bus-master fencing;
PCI core cannot be refused by returning from its VOID remove callback. See
WR1200JS-IOT-PCI-REMOVE-BOUNDARY-2026-11-01.md and the terminal-quiescence
inventory. No memory-retention or successful host-test result proves safety
after core unbind. Next work remains device-specific terminal fencing,
callback/owner retirement and firmware-policy completion evidence.

## Candidate follow-up — sender wired, default guard retained

The isolated v40/composed checked MT7603 close now calls
`wr_iot_send_radio_off_checked()` on the path that reaches the checked command.
It uses `wr_iot_prepare_radio_off()` plus the existing opt-in message-owned
result handling in `AndesSendCmdMsg`; the legacy `CmdRadioOnOffCtrl` callback
and production macro setting remain unchanged. The auxiliary-family preparer
accepts the exact sender implementation without injecting a duplicate.

The `LOAD_FW_ONE_TIME` early refusal remains in place before any queue, MAC,
MCU, PDMA or interrupt mutation. Host fixtures compile and run both modes:
without the macro they exercise ticket/order/failure-retention/no-replay; with
the macro they assert immediate failure and no mutation. The sender fixture
covers null adapter, allocation failure, send failure and success. These are
candidate/source checks only. They do not prove that the target firmware
accepts this command under the macro, that RF emission stops, or that DMA/IRQ/PCI
owners are quiesced. No target module/image, router operation or runtime
acceptance is claimed. Keep the candidate isolated until firmware-policy and
terminal-removal evidence support promotion.

## Full isolated module follow-up

The current 75-stage candidate, strict merged then layered with the workflow's
existing WNM/PMF preparation, passes isolated MIPS module compilation/MODPOST/
link. This supersedes older statements above that no target module was built.
The linked module still emits an 8-byte unconditional-FALSE
`wr_iot_mt_radio_off_checked` under effective LOAD_FW_ONE_TIME; the checked
sender exists as a separate 0xdc-byte symbol but is unreachable from that
entry. Disassembly and module hash are in RADIO-ON-MODULE-LINK JSON. Kernel
Module.symvers, full firmware image and runtime acceptance remain unverified.
Successful linking does not close the default radio-off compatibility gap.
