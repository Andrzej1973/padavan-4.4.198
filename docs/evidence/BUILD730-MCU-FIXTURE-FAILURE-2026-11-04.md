# Optional 730: stale MCU lifetime fixture call

Run 41760866396 dispatched from b48c317b and verified source c606e1c.
Firmware completed; optional job 126348046526 failed in Compile isolated
merged IoT MT7603 candidate, before MIPS/module or full WSC compilation.
Original log identifies check-mcu-sequence-lifetime.py: its mock destroy
called wr_iot_mcu_message_drop(a,slot), but the generated helper requires
the third uncertainty argument after the timeout quarantine change.

Updated the normal-completion fixture to pass uncertainty=0 and explicitly
check the expected generated signature. Fresh bounded/reserved generation
then passed all four actual CI checks: allocator, release, lifetime and
destructors under ASan/UBSan. Temporary source and binaries removed.

Monitor run 41762174503, artifact 13290537776, named the correct failed step
but scanned only the first 256 KiB and missed the causal compiler error,
reporting earlier nonfatal patch/retry noise. Our branch already contains
the bounded 16 MiB tail fix (741e6090/53dd84d0); deployed default-branch code
has not incorporated it. Extended its long-log regression with this exact
too-few-arguments diagnostic after more than 16 MiB. Built the actual Nim
monitor locally and all offline monitor tests passed, including failure-only
filtering and deduplication. Fixture/cache/binary removed. No periodic wakeup
or default-branch mutation was made.

Standard 41760759126, ABI 41760759016 and services 41760752739 succeeded for
b48c317b, confirming the new fetch path completed in that standard run.
Full optional verification must use the new fixture-fix source revision;
rerunning the old c606e1c source would preserve the fixture defect.
