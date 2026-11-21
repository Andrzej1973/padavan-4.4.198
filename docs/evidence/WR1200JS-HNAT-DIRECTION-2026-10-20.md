# HNAT direction predicate comparison — 2026-10-20

The live #474 module path is
`/lib/modules/4.4.198/kernel/drivers/net/ethernet/raeth/mtk_hnat/hw_nat.ko`;
its SHA256 is recorded in the private raw snapshot. Source inspection uses pinned
revision c25283e915a2a00a763774dd255b14aff997285e. This is not proof of byte-for-byte
identity between compiled #474 and an untransformed upstream source checkout.

Both kernel driver copies have a `do_ge2ext_fast` predicate in hnat_nf_hook.c.
The raeth copy includes `IS_EXT(dev)` alongside LAN/WAN/PPD; the mediatek copy
allows only LAN/WAN/PPD. The shared conditions are a hashed skb and reason
HIT_BIND_FORCE_TO_CPU (0x16). The branch is documented as GE-to-external traffic.
`IS_EXT` uses get_index_from_dev, i.e. membership in the HNAT external-device map.

The exact two source macros were extracted and compiled with native GCC under
-Wall/-Wextra/-Werror. All 64 device-class/hash/reason combinations were compared.
Only one differed: external-only input, hashed=1, reason=0x16. Raeth accepts
that packet into the fast path; mediatek does not. The adjacent JSON preserves
the exact predicates, source-file hashes and differing case. This is a bounded
host predicate experiment; it does not emulate skb ownership, netfilter, PPE,
Wi-Fi firmware or traffic on the router.

This difference is consistent with the retained 981 reason0x16 messages on
ra0/rai0, but does not establish causation. The raeth handler calls
`do_hnat_ge_to_ext`; on failure it logs rate-limited KERN_WARNING and returns
NF_DROP. That helper uses a FOE entry's act_dp to find an external device and
may invalidate stale mappings. The caller's ingress predicate therefore
matters, but changing it without verifying the full ping-pong contract could
break intended offload.

The existing RC patch sends hw_nat_register=0 in mode2 and 1 only in mode1;
its current tests mock successful command dispatch. They do not prove driver
acceptance, external-map state, stale FOE cleanup or hardware behavior. Mode2
and loaded hw_nat alone cannot prove that every Wi-Fi path bypasses PPE.

Next source checks: follow each radio's hw_nat_register set handler and whether
it changes HNAT ext_if membership, rx/tx hooks or only another registration;
trace get_index_from_dev/act_dp lifetime and incoming skb ownership; compare
live module to #474 image/source before claiming an exact cause. Then build a
scoped driver candidate and test packet ownership/failure cases before a
supervised traffic test. Keep mode1 manual Wi-Fi trial and mode2 factory policy
intact. No production predicate, router setting, service or log level was changed.

Unrelated CI repair in the same work interval: #495's KVR emitter mock failed
after source getter adaptation. Commit 6cb5f3d fixes both getter variants;
32 local C emitter combinations pass. Evidence is WR1200JS-BUILD495-KVR-FIXTURE.md.
