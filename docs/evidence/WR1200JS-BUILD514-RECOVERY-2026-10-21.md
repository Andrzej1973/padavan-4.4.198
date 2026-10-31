# WR1200JS build #514 — recovery after #513

GitHub Actions [run #514](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39644862386)
completed successfully for source commit
`a6edff845ddbebd90e2833800445757290c921b9`. Its `select`,
`build-wr1200js`, `downloads` and `firmware-zip` jobs all succeeded.

The build job passed firmware compilation and the Privoxy final-image gate
that failed in #512/#513. It also passed the target BusyBox audit, the
image Stubby DNS lookup under QEMU, DoH image packaging, discovery/KMS status,
StrongSwan exclusion and ZeroTier persistence checks. The artifact list
includes `privoxy-image-checks` (`12368535292`),
`padavan-linux-4.4.198-wr1200js` (`12366988247`),
`padavan-4.4.198-router-downloads` (`12367447199`) and the firmware ZIP
`WR1200JS_4.4.198.9-514_149647e5_TEST` (`12367627054`). The workflow's
selected-board and ZIP jobs passed; these are the CI verdicts for this exact
source revision.

The causal sequence in recent failed builds is now closed at the CI level:

- #489/#491: toolchain `nm` lookup; #492 passed.
- #493: Lua shared-library fixture in the BusyBox audit; later image audits
  passed.
- #494–#496: KVR getter fixture; #497 passed preparation.
- #498: KVR options absent from effective build-tree config; the follow-up
  source correction reached the later MT76x3 compiler gates.
- #499/#500: MT76x3 WNM/PMF and FT/IGTK guards; #501–#504 built successfully.
- #505–#508: VPN pruning/page-hook assumptions; #509–#513 passed VPN
  preparation.
- #509–#511: QEMU dnsmasq random-seed fixture; #512–#514 passed the target
  DNS checks.
- #512/#513: Privoxy verifier searched only the obsolete two-argument Apply
  call; isolated checker correction `a6edff8` passed in #514.

Failures in downstream required-image/download and diagnostic-upload steps
were consequences of the first failed gate in each run. The separate Band
Steering ABI #489 for `a6edff8` also completed successfully.

This is build and image evidence. It does not verify physical-router service
behavior, WebUI Apply/save, Wi-Fi clients, persistence or flashing. No router
setting, service or firmware was changed during this repair.
