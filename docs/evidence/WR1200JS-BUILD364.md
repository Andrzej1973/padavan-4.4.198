# WR1200JS build 364 review — 2026-10-17

Firmware run https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39003429600
and service run 39003429531 (#141) both completed successfully at
1eaa5a557354be06231d5bb73741498ded698c7d.

Downloaded image WR1200JS_4.4.198.9-364_1eaa5a55.trx is 12,575,299 bytes.
Locally computed SHA256 matches the original image report:
5d329a6d3b22248a82dad54b7a7366218e8cbcc5e64a69bcf0b7207a8c576a74

Original small reports are retained in build364/. Both readback helpers are
MIPS ELF (WG 50,496 bytes; AWG 74,692 bytes). Six read-only QEMU gates passed:
missing interface, legacy interface refusal and unresolved hostname refusal for
each protocol. Ten shipped MIPS manager/store/validator cases also passed.
These checks establish packaging/execution and bounded rejection, not matching a
configured physical interface or working concurrent tunnels. No device changes.

Latest ten firmware runs reviewed: 359–364 and 357 succeeded; 358 failed native
validator compilation (resolved by 359), 355/356 failed exact-target BusyBox
server-export checks (resolved by 357). Recent service failures 138/139 were
fixture build dependencies, corrected in successful 140/141. No pending runs
were present among these reviewed results. This is not physical acceptance.
