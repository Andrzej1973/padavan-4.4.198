# TxS and beacon builder composition

check-txs-builder-composition.py extracts BcnTxSHandler and the final candidate
producer/gate headers. It invokes the callback in reopened state, observes its
IDLE update, then exercises actual builder admission with busy, unknown and
zero injected DMA counts. Busy/unknown refuse admission despite IDLE and roll
back the producer pin. Zero permits a pin, released explicitly by the fixture.
DBG and non-DBG native ASan/UBSan pass. The fixture uses the vendor UCHAR BssidNum.

This checks composition of existing safety gates; it changes no driver policy.
Injected locks/DMA and synthetic report do not establish hardware completion,
actual duplicate delivery, RF/FIFO retirement or permission to release isolation.
The stale PID/uncorrelated callback limitation remains unresolved. No ACK protocol
or stale ACK protection is changed. peer82 CI runs this after final API staging.
Evidence: evidence/WR1200JS-IOT-TXS-BUILDER-COMPOSITION-2026-11-08.json.
