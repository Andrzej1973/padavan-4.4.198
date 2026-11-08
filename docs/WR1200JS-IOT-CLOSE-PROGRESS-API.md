# Staged CLOSE progress API

This Linux-only proposal is not installed in the private ioctl dispatcher.
It does not modify MCU firmware or ACK handling. Current production activation
must remain disabled until common dispatch, ownership and target checks pass.

Operation 10 requests a single CLOSE. Operation 13 advances reference retirement
of an already owned CLOSE. They deliberately reject each other's packets.
Both use a 64-byte request: `WRI2` at bytes 0–3, operation at 4, zero bytes
5–7, original successful OPEN nonce at 8–23, big-endian unsigned 64-bit adapter
epoch at 24–31, device generation at 32–39 and OPEN token at 40–47, zero bytes
48–63. No password, SSID, kernel pointer or task handle crosses the boundary.
Identity comparison occurs before narrowing to target unsigned long.

The common ioctl must check RTNL, CAP_NET_ADMIN in the device namespace,
MT7603 target/interface before dispatch. The private `ifreq` transport has no
user length field: it copies a fixed 64-byte buffer and the decoder checks its
format. Truncated/unmapped user memory must fail the copy. The staged
reply helper assumes these checks; a separate uninstalled transport implements
them for operation 13 with exact third-BSS identity before copying. it is not a standalone privileged endpoint.
Progress must work after administrative DOWN and must never call dev_close,
dev_open, restart the radio, scan channels or allocate another CLOSE ticket.

The progress helper requires exclusive RTNL serialization and registration/
adapter lifetime across the call. It matches the original successful OPEN
receipt and active CLOSE identity. An outstanding tracked task handle permits
only reconciliation after fixed-body refusal and core completion; a running
borrowed designation returns EINPROGRESS. Otherwise it attempts the fixed
retirement launch. An ambiguous wake keeps the caller reference in the owner.

| Return | Meaning |
| --- | --- |
| 0 | Coherent module-reference handoff completed in current radio epoch, with no reset/retiring/PM transition; active OPEN fence remains |
| -EINPROGRESS | Task launched or exact designated task still outstanding |
| -EAGAIN | Core exit not observed, or one refused-task reference reconciled; caller may explicitly query later |
| -EBUSY | Identity, readiness, ownership or RTNL precondition not satisfied |
| -EUCLEAN | Ambiguous transition; retain recorded ownership and inspect state |
| -EINVAL | Malformed request or invalid helper arguments |

Other underlying creation errors can propagate. A caller must not automatically
repeat operation 10 after any progress result. Zero is not evidence of RF/FIFO
silence, safe buffer reuse, isolation removal, permission to reopen or device
acceptance. Those contracts remain separate and unresolved.

Host tests compose actual staged finish, netdev return, launch, task refusal,
reconcile and progress bodies with injected kernel primitives. They do not
execute the scheduler, hardware or a real ioctl. The MIPS target probe includes
the helpers but its result must be tied to the exact source revision. Physical
WR1200JS acceptance remains outstanding.
