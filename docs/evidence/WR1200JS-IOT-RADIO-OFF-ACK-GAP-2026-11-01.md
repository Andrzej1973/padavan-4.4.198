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

Current checked radio-off hardware path still invokes legacy
CmdRadioOnOffCtrl, and wr_iot_prepare_radio_off has no invocation beyond its
definition in this candidate tree. Next: reuse the existing checked message
builder/result path with a narrowly scoped send wrapper after proving exact
lifetime and caller ownership. LOAD_FW_ONE_TIME compatibility and terminal
PCI quiescence remain independent blockers; this correction does not close them.
