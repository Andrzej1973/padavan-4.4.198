# IoT ABI checkpoint — 2026-10-18

GitHub Actions [run #449](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39114663222)
completed successfully for project commit
`b65acf6081ebe9e73e8fea7501af346f7473dcd9`. Its
`band-steering-mips-abi` artifact is ID `12131499189` (archive digest
`sha256:2e41ae1b4efc61b33424191c45c6519cd0126f6f3cf799466379ad151464783f`).

The job passed the synthetic radio-capacity self-test, actual RC/profile
snapshot checks, IoT activation sequencing with retained recovery, request
snapshot and request-stage checks, firewall/network helper checks, and MIPS
compilation of the staged IoT components. The activation fixture uses an
injected backend; it proves ordering/recovery behavior in the controller, not
the production operations on the router.

## Remaining acceptance gaps

- The source-integration report still marks production `activation_integrated`
  false. The service transaction/write journal and complete dnsmasq/service
  rollback are not bound to a production activation path.
- The main firmware workflow explicitly rejects the IoT RC sources, so this
  ABI run is not firmware image evidence.
- No physical third BSS, simultaneous main/guest/IoT use, DHCP/DNS client flow,
  IPv4/IPv6 isolation under the target kernel, WAN access, settings persistence,
  or restart/recovery behavior has been accepted on the router.
- The read-only device snapshot from 2026-10-18 did not find `ra2`; that is a
  runtime observation for that sample, not evidence that a future image cannot
  create it.

Conclusion: the ABI/controller checkpoint passes, but the separate IoT Wi-Fi
deliverable remains incomplete and is not ready to enable or flash.
