# Vendor group-key path and defined peer-byte packing

Pinned SDK `c25283e915a2a00a763774dd255b14aff997285e`, vendor mt76x3 only.
The separate source report records exact function lines and file identities.

`SSID` restarts the AP. `SSIDSingle` calls per-BSS security, group-key and beacon
helpers. `WPAPSK` updates the PMK/key text, without providing that complete
transaction. Raw `MBSS_Open` does not provision a missing new group key.
These setters must not become an unowned Classic Apply shortcut.

The group-key chain reaches `WPAInstallSharedKey` and
`CmdProcAddRemoveKey`. In this implementation the latter writes WTBL directly
through MMIO. It does not send an MCU command in its body. The HIF_MT branches
of older shared-key/attribute helpers return without installing the key.
Therefore a scoped closed-profile implementation should investigate and verify
this existing host WTBL path, rather than require unavailable ROM specifications.

## Minimal correction

The add and remove branches both pack four peer bytes with this expression:

```c
dw1->word = CmdKey.aucPeerAddr[0] + (CmdKey.aucPeerAddr[1] << 8)
          + (CmdKey.aucPeerAddr[2] << 16) + (CmdKey.aucPeerAddr[3] << 24);
```

Integer promotion makes the last shift signed. The original extracted function
triggers UBSan for broadcast byte `255 << 24`. The isolated candidate producer
now replaces exactly these two expressions with:

```c
dw1->word = (UINT32)CmdKey.aucPeerAddr[0]
          | ((UINT32)CmdKey.aucPeerAddr[1] << 8)
          | ((UINT32)CmdKey.aucPeerAddr[2] << 16)
          | ((UINT32)CmdKey.aucPeerAddr[3] << 24);
```

This preserves byte placement and register addresses while defining the shifts.
There is no queue, ACK, DMA ownership, radio timing or teardown-state change.
It is not evidence that this UB caused any previously observed router failure.
Only the isolated candidate is transformed; main-image promotion is separate.

## Executed evidence

`check-vendor-group-key-path.py` extracts the complete native writer and WTBL
lookup, uses native key/WTBL declarations and cipher constants, and supplies
synthetic MMIO/configuration. No MCU transport implementation is linked.
The original stops under UBSan with the expected high-byte diagnostic.
The corrected writer passes GCC O2/Werror/ASan/UBSan with
`UBSAN_OPTIONS=halt_on_error=1`, all 256 high-byte values, exact AES key and WTBL
address/value traces, failed-store injection, lookup refusal, invalid-WCID
clamping and BSS/WCID mismatch observations. Drift and repeated preparation
are refused. Native source blob IDs were compared with GitHub at the pinned SDK.

The actual builder/producer DMA composition and periodic first-beacon checks
also passed. Python/YAML/shell syntax and scoped whitespace checks passed.
The archive-specific no-host bundle checker was not executed: it requires a
prepared-source archive, and no matching new target archive exists yet.
The new host regression runs in ABI and optional preparation before target build.

## Remaining completion work

The raw helper is void: a dropped synthetic MMIO write produces no failure
return. Native lookup clamps an invalid WCID while the key-material address
uses the raw index. BssIdx does not itself validate the supplied group WCID.
A new closed-profile transaction must validate exact ra2/table identity and
ownership, handle partial mutation/readback failures while staying closed, and
publish applied only after its own completion checks. This correction does
not implement that transaction or complete the original ACK/TxS blocker.

Standard1386 and ABI935 succeeded for prior `5fa12e65`. Optional1387
`44318237538` now verifies that revision, including its new selector linkage
proof. Those runs do not cover this later packing change. New target/feature
compilation, embedded-image verification and separately authorized physical
acceptance remain required. Router unchanged; Modern remains paused.
