# WR1200JS IoT and HWNAT isolation audit

Status: source and selected image evidence; physical isolation unverified.
No global HWNAT disable or router configuration change was made.

- Standard `0dc0a6b`, run42557592602: actual ROMFS module is
  `raeth/mtk_hnat/hw_nat.ko`, ELF32 MIPS, independently hashed. Embedded DTB
  external devices omit ra2 and br-iot. Wired HWNAT remains enabled.
- Optional `6fa32ef`, run42554625088: saved actual target macro records define
  RA_NAT_NONE and omit NEW_ARCH in the inspected TUs. These are different source
  revisions; neither substitutes for current final-image verification.
- Vendor MBSS creates zeroed private netdev ops. No ndo_hnat_check reference was
  found in pinned MT7603 sources or inspected IoT generators. Bridge ingress
  classifies physical input before the external fastpath; unknown nonbridge
  input without that callback is not EXT. Runtime traversal is still unproven.
- Adapter-wide registration and ordinary OPEN can register devices if enabled
  by future compile flags. Unregister alone is not a hardware flow drain.
  NETDEV_GOING_DOWN invokes global BIND invalidation, not selective IoT cleanup.
- Debugfs external_interface is read-only. Dynamic registration through kernel
  hooks and existing flows after policy changes remain acceptance considerations.

`tools/verify-wr1200js-config.py` now requires the currently audited kernel
split: HW_NAT=y and RA_NAT_NONE=y. The gate preserves assumptions; it does not
prove compiled driver macros, final DTB contents or packet isolation. Changing
these assumptions requires renewed IoT admission/flow-lifetime analysis and
appropriate build and device evidence. The owner-selected HNAT runtime mode
and existing Main/Guest offload behavior are not rewritten by this check.

Remaining acceptance: exact latest target macros/module/DTB; actual interface
ops and bridge traversal; bidirectional IoT-to-LAN denial with Main/Guest
unchanged; WAN/DHCP/DNS behavior; policy/subnet changes with existing flows;
IPv6 DROP behavior; no acceleration bypass. Device tests need separate owner
authorization. The Wi-Fi RF/late-TxS reopen blocker remains a distinct issue.

Evidence files under docs/evidence: HWNAT-SOURCE-PREFLIGHT,
HWNAT-IMAGE-0DC0A6B, HWNAT-MODULE-0DC0A6B, HWNAT-DTB-0DC0A6B,
HWNAT-TARGET-FLAGS-6FA32EF and HWNAT-CONFIG-GATE-LOCAL (2026-11-09).

The uImage verifier now also inspects its actual LZMA kernel and embedded DTB.
It rejects ambiguous/malformed DTBs, IoT external-device entries ra2/rai2/br-iot,
missing Main entries and changed eth2/eth3 mapping. Decompression is bounded.
Synthetic mutations and an independently CRC-repaired mutation of the actual
0dc0a6b image are checked locally: the modified image passes all older structure
checks but is refused by the new DTB policy. This image gate does not establish
dynamic registration behavior or physical forwarding isolation.

The parser limits kernel output to64MiB, decoder memory to128MiB, individual
DTBs to2MiB, candidate parsing to8MiB/128 attempts, depth to64, nodes to8192
and properties to16384. The workflow runs the regression when the selected
source verifier contains this gate. Historical optional source revisions retain
their own verifier behavior; they do not establish the new policy check.
