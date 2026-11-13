# Experimental recovery-only OPEN receipt

A clean owned OPEN can retain a configuration receipt when its first beacon
publication wait times out. Normal query11/reply12 deliberately refuses that
case. Recovery query15/reply16 exposes only the token needed for CLOSE, using
the unchanged CLOSE admission predicate. It never certifies successful ON.

This Linux-only extension uses ioctl `0x89fd` on fixed `ra2`; it changes no
firmware protocol. The experimental common entry holds RTNL and checks
CAP_NET_ADMIN and MT7603 before the fixed64-byte input copy. The reply checks
exact third BSS, current registry/receipt/nonce/epoch/generation, Main readiness
and absence of control, reset, PM, removal, poison or active CLOSE/probe.

The64-byte wire retains magic WRI2, opcode at byte4, original16-byte nonce at
bytes8–23. Query15 reserves all other bytes as zero. Reply16 contains nonzero
big-endian64-bit epoch, generation and token at bytes24,32,40; bytes5–7 and
48–63 remain zero. Normal ON, CLOSE and CLOSED decoders reject this reply.

RC `wr_iot_driver_open_recovery_read` validates the original identity and gives
CLOSE_BEGIN a recovery token. Normal `open_submit` still uses strict query11.
CLOSE itself revalidates ownership before mutation; no OPEN is retried.

Only the16-path no-host experiment installs the recovery endpoint. Production
activation and startup-baseline rollback remain unbound. Host checks are not
MIPS compilation, full image verification or physical WR1200JS acceptance.
