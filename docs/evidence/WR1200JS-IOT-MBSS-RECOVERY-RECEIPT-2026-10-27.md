# IoT MBSS recovery completion receipt — host contract

This is a host-only correction to the deferred MBSS recovery model. It does not bind a kernel worker, change the production driver, or prove device behavior.

The checked MBSS close executor calls `wr_iot_radio_finish`, consumes the exact interface reference and writes `close_stage=4` while holding the adapter transition lock. The previous `wr_iot_mbss_recovery_mark_completed` additionally required `radio->busy==0` and `radio->retired_serial==owner->close_serial`. A subsequent radio operation may begin or retire before the recovery worker observes completion. That global state would reject an already completed close and retain its deferred netdev/adapter owner indefinitely.

The host contract now accepts the durable per-record receipt: same device, generation, open token, close serial and recorded ticket, `WR_REF_IDLE`, stage 4. The checked executor must write these fields atomically before another ticket can alter global radio state. The fixture passes with a newer retired serial and another operation busy, and rejects the same record at stage 3. Strict C11 `gcc -Wall -Wextra -Werror -pedantic` compile and execution passed locally.

Before kernel binding, verify that slot reuse cannot erase this receipt before the worker consumes it; keep the netdev and adapter pinned, join the worker during PCI removal, and prove beacon DMA/TxS retirement. Candidate target compile #629 is independent of this host-model edit.
