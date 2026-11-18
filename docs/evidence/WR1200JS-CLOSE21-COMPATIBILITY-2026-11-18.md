# Explicit Linux CLOSE21 compatibility contract

The previous paired candidate encoded retryable pre-admission EBUSY using
legacy CLOSE10. Pairing metadata guarded coherent images, but did not make
the changed interpretation explicit at the ioctl operation boundary.

New RC submits operation21 in the existing fixed64 WRI2 Linux transport.
It carries the same original OPEN nonce/epoch/generation/token. Legacy10
encoding and decoding remain unchanged and reject21. The new common
privileged dispatcher explicitly routes10/21 to the checked CLOSE entry.
Only21 permits the RC client to classify exact ioctl -1/EBUSY plus successful
fd close as NOT_SUBMITTED. Legacy10 errors remain uncertain. There is no
fallback from21 to10. Progress13/release14 are unchanged. Every error after
admission/dev_close remains normalized to EUCLEAN, prohibiting CLOSE replay.

WRI2 opcodes19/20 already identify Main-DOWN observations;21 was checked against
existing wire declarations/routes before reservation. This is not a MediaTek
firmware opcode and changes no MCU ACK semantics.

The wire fixture checks format, lengths, reserved bytes, cleared output,
null input and mutual10/21 rejection. The actual generated dispatcher is tested
both with21 routes and with its predecessor10/progress routes: the predecessor
rejects21 through its real fallback query decoder before calling any executor.
The kernel/client/controller composition simulates a legacy decoder and
confirms no mutation and no silent fallback. Legacy10 EBUSY stays uncertain;
new21 pre-admission busy can defer, whereas post-admission busy, failed fd close,
refused finish and unexpected positive syscall replies cannot replay CLOSE.

Driver and RC manifests require integer close_busy_request_opcode21 in addition
to the earlier typed busy/timer metadata. Pairing rejects missing, false,
float21, string21 and wrong opcode values. Host pairing/ROMFS negative checks,
wire/client/entry/composition tests, common-dispatch compatibility and complete
edit/view suite passed. These use native host compilation and boundary actors;
no target image or physical acceptance for this change is claimed.

Prior standard1391 and ABI938 succeeded for2c998421. Optional1390 succeeded
for7c3cbc55, including the corrected RC all-target map preparation. Its artifact
still needs independent map/provider/image inspection. New optional for2c
was dispatched after inspecting all standard1391 jobs. Neither run covers
this later CLOSE21 revision. Router unchanged; original ACK/TxS/PCI/DMA/IRQ
acceptance and full IoT provisioning remain unfinished.
