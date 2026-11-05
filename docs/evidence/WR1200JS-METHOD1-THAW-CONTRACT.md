# Pending Method1 bootstrap handoff

Source inspected: isolated candidate generated from repository ae122707.

The checked PCI controller initialization clears
`fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD`. Both AndesDequeueAndKickOutCmdMsgs
and the send-body path reject commands while that flag is clear. Hardware
preparation ends with constructors frozen and does not set the flag. Therefore
calling hardware preparation from Method1 alone cannot complete downloading.

The next implementation must validate the exact private ticket, completed
hardware stage6/state2, controller/RX/IRQ/DMA ownership, ticket-bound retirement
receipt and empty sender before setting the transport flag and releasing only
the private constructor freeze under transition/sender locks. Normal sender
admission and data tasklet/RX fences must remain closed. Failure must block
IRQ rearm before DMA stop and retain uncertain resources. A firmware start
ACK and RUN readback require separate completion before normal admission.

Method1's generic done path also writes SCH_REG4. Its ordering relative to
bootstrap failure masking/stop must be covered when binding this transition.
The existing active-bootstrap init refusal remains until final promotion is
implemented and verified. This document records source analysis, not an
implemented thaw, firmware epoch guarantee or runtime result.
