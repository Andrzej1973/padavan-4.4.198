# ZeroTier 1.16.2 production image evidence

Verified on 2026-10-04 using [run 37173482651](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37173482651), source commit `676e1f3b36d4a3d7e3eb1099b68d6c8ee2470b0b`, job `111351239008`.

## Proven build results

The WR1200JS production build, effective configuration, image structure, WPAD, Stubby, Privoxy, DoH, RSSI Kick and ZeroTier image gates passed. The image was uploaded. At evidence collection the complete workflow was still running the isolated MT7621 systick candidate check; this report does not assert overall workflow completion.

Downloaded artifact `11292488040` (`zerotier-image-checks`) confirms source revision/version and executable code match, target ELF/dependency closure and lifecycle helper presence. Its `errors` list is empty; `runtime_verified` is false. The lifecycle-helper gate checks presence, not service behavior or the unfinished new WebUI/monitor/policy implementation.

ZeroTier binary SHA256: `594fbca15fc8416f4c4dd52cca43068f28968d2c702db539d4dff6bc4e0f8270`.

Required target libraries are included: `libatomic.so.1`, `libgcc_s.so.1`, `libc.so.0`, `ld-uClibc.so.1`. The uClibc implementation is 1.0.43.

## Image identity

From downloaded diagnostic artifact `11292248442`:

- Image: `WR1200JS_4.4.198.9-100.trx`
- Size: **13,269,860 bytes** (approximately 12.66 MiB)
- SHA256: `1254518f55d1cc6cc7d5463ebe15f3cc681b6eb4481d57eb8aef9d7a4c58f0b3`
- Artifact ZIP SHA256: `818d4634fec65534890a211bc8c160f5b36981de80663fbd0ac64026fb448468`
- ZeroTier diagnostic ZIP SHA256: `63562b219b26158a7b0097bf612eb621fac6e509f7ee79b8ec2c232b00a1de8b`

These are compile/package observations. Device boot, both radios under load, Hardware NAT, VPN services and actual ZeroTier connectivity remain unverified for this image. No remote flash or reboot was performed or authorized.
