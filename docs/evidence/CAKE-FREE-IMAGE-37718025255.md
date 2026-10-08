# CAKE-free WR1200JS image evidence

Inspected on 2026-10-08. Run 37718025255 source:
65e14f7653730de6ceec6d5f367eb039c6cf5a0d.
The workflow was still running isolated kernel checks at inspection time;
this is not a claim that the entire workflow completed.

Downloaded artifact 11525372174, padavan-linux-4.4.198-wr1200js:

- Image: WR1200JS_4.4.198.9-100.trx.
- Bytes: 13051032.
- SHA256: 5a797629a319cab7cfc91919b572af2a8608a6f227f29295701e08bb2dc12128.
- Image report passes uImage magic, product ID, header/payload CRC,
  declared length and configured size range. These checks do not prove boot.
- Requested and effective CONFIG_FIRMWARE_INCLUDE_SQM=n.
- Configuration report: no mismatches or pending options.
- Actual kernel-effective.config: CONFIG_NET_SCH_CAKE is not set;
  CONFIG_NET_SCH_FQ_CODEL=y.
- Actual driver selections: CONFIG_FIRST_IF_MT7603E=y and
  CONFIG_RT_SECOND_IF_MT7612E=y.
- Both production Band Steering kernel selectors remain disabled.

Job 113118985568 completed the isolated full driver and full rc compilation
steps successfully. These are separate candidates, not installed steering
support in the normal image. FQ-CoDel configuration does not prove active
traffic shaping or performance. No router flash, boot or Wi-Fi runtime test
was performed.

Separately, ABI run 37720569696 completed successfully at source
29025307bc985ea0728dda239d4b66e0748f06cc. Job 113127019827 logs confirm all
seven radio-read guard cases: valid source plus added/removed sites for each
of nvram_wlan_get, nvram_wlan_get_int and nvram_get_int. The fixture requires
rejected files and the original source to remain unchanged.

