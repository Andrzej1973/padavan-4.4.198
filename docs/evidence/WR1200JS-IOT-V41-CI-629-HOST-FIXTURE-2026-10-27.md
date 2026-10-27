# Optional IoT v41 run #629: host fixture failure

## Evidence

- GitHub run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40447432208
- Head: `48ffaef23f8a12728bcfb32bb1c8397a9d6f524e`.
- Failed job: `Compile isolated merged IoT MT7603 candidate`, job
  `122001987197`, at 2026-10-27 04:16:24Z.
- Compiler diagnostic: `tools/iot/check-mbss-close.c` includes generated
  `wr-iot-mbss-close-checked.inc`; its line 233 called `wake_up_all`, but the
  standalone host mock did not declare that function or its adapter field
  `wr_iot_ticket_wait`. GCC stopped on implicit declaration and missing field.
- The downstream artifact contained only binding metadata and `config.log`;
  #629 did not produce an MIPS module.

## Narrow correction and check

`tools/iot/check-mbss-close.c` now models the ticket wait field and a wake
function that asserts it runs outside the mocked IRQ lock. It asserts zero
wakes on the failed close path, exactly one after successful retirement, and
no additional wake on the idempotent repeat close. This changes the host test
only; it does not change the candidate or production driver.

Local MinGW GCC compiled and executed the generated v41 fixture with
`-std=c11 -Wall -Wextra -Werror -DWR_IOT_V40=1` in three variants: base,
`MT_MAC`, and `MT_MAC+RTMP_PCI_SUPPORT`. All three returned success.
`git diff --check` passed for the changed fixture.

## Limit

The local host check repairs the observed #629 blocker. A new target run is
needed to confirm the MIPS compile and the remaining candidate gates. There
is no production backend or router acceptance from this result.
