# Complete WSC feature build: preparation evidence

The pinned mt76x3_ap wrapper Makefile selects full WSC objects through
CONFIG_MT7603E_WSC_INCLUDED and CONFIG_MT7603E_WSC_V2_SUPPORT. The helper
uses those make overrides in an exclusive copied kernel tree, then checks
effective macros and defined WSC/MBSS functions in the linked module.
This is separate from the production configuration and baseline artifact.

## Local orchestration check

Executed the actual ci-compile-wsc-feature.sh against a temporary miniature
kernel tree, with mocked make/compiler/readelf. Verified:

- Full-module target and both WSC overrides reach make.
- Feature build operates on the exclusive copy; every baseline file retains
  its original bytes after success and failure.
- The actual checker/report path preserves candidate revision and requires
  effective WSC/AP/V2/KTHREAD macro evidence.
- Successful orchestration emits its report; injected make failure emits no
  success report and returns failure.
- Temporary feature tree is removed on both exit paths. The whole miniature
  fixture was then removed by TemporaryDirectory.

The fixture supplied synthetic ELF bytes and symbols. It proves orchestration
only, not actual compilation, linking, exported dependency closure or kernel
behavior. Shell/embedded Python syntax and whitespace checks also passed.

Additional input check: actual kernel.config from artifact 13264066070
selects MT7603E_RLT_AP_SUPPORT=m and MT76X3_AP=m. The helper now requires
both before invoking module-only Kbuild. Pinned wrapper uses ../mt76x3
objects and relative include paths resolved from the copied kernel root.

The result generator additionally requires all six WSC/crypto objects
(wsc, wsc_tlv, wsc_ufd, wsc_v2, crypt_dh, crypt_biginteger) as relocatable
little-endian MIPS ELF, with source/object/Kbuild-command hashes. A synthetic
report fixture verified six records and failure without a success report
when wsc_v2.o is missing. This tests report logic, not real object linking.
Temporary fixture removed. Updated helper target execution still pending.

## Pending acceptance

Run the published helper in peer82 optional CI, inspect original logs on any
failure and compare the failure-monitor report. Independently validate the
resulting real MIPS module, source/config provenance, required effective
macros and symbol definitions. Full linked WSC support and runtime remain
unverified until those separate stages provide evidence.
