#!/usr/bin/env python3
"""Extract the staged TxS removal function into an executable host fixture."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path, help="assembled partial driver tree")
    parser.add_argument("output", type=Path, help="new C fixture path")
    args = parser.parse_args()
    source = (args.candidate / "tx_rx" / "txs.c").read_text(encoding="utf-8")
    functions = []
    for signature in (
        "INT32 AddTxSStatus(RTMP_ADAPTER *pAd, UINT8 Type,",
        "INT32 RemoveTxSStatus(RTMP_ADAPTER *pAd, UINT8 TxSPid,",
        "static INT32 WrTxSCompleteClaim(RTMP_ADAPTER *pAd, UINT8 Pid)",
        "INT32 CancelTxSReservation(RTMP_ADAPTER *pAd, UINT8 Pid,",
    ):
        if source.count(signature) != 1:
            raise SystemExit(f"Cannot identify staged TxS function: {signature}")
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        functions.append(source[start:end])
    header = r'''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef int INT32;
typedef uint8_t UINT8;
typedef uint16_t UINT16;
typedef uint32_t UINT32;
typedef unsigned long ULONG;
enum { TXS_UNUSED = 0, TXS_USED = 1, TXS_STATUS_NUM = 256 };
#define TXS_CLAIMED 2
#define TRUE 1
#define TXS_TYPE1 1
#define FC_TYPE_MGMT 0
#define SUBTYPE_BEACON 8
#define HW_BEACON_MAX_NUM 16
typedef struct { UINT8 TxSPid, State, Type, PktPid, PktType, PktSubType; UINT16 TxRate; UINT32 Priv, Generation; } TXS_STATUS;
typedef struct { int held; } NDIS_SPIN_LOCK;
#define RTMP_SPIN_LOCK_IRQSAVE(lock, flags) do { *(flags) = 0; assert(!(lock)->held); (lock)->held = 1; } while (0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock, flags) do { (void)*(flags); assert((lock)->held); (lock)->held = 0; } while (0)
typedef struct { UINT8 TxSPid; ULONG TxSFailCount; TXS_STATUS TxSStatus[TXS_STATUS_NUM]; NDIS_SPIN_LOCK TxSStatusLock; UINT16 BeaconCallbacksInFlight[HW_BEACON_MAX_NUM]; int BeaconCallbackAccountingFault; UINT32 ReservationGeneration; } TXS_CTL;
typedef struct { TXS_CTL TxSCtl; } RTMP_ADAPTER;
'''
    body = r'''
int main(void) {
    RTMP_ADAPTER adapter = {0};
    UINT8 type = 0, pktpid = 0, pkttype = 0, subtype = 0;
    UINT16 rate = 0;
    UINT32 priv = 0;
    UINT8 issued = 77;
    UINT32 generation = 0;
    unsigned int i;
    adapter.TxSCtl.TxSPid = 12;
    adapter.TxSCtl.TxSStatus[7].State = TXS_USED;
    adapter.TxSCtl.TxSStatus[7].Type = 1;
    adapter.TxSCtl.TxSStatus[7].PktPid = 2;
    adapter.TxSCtl.TxSStatus[7].PktType = 3;
    adapter.TxSCtl.TxSStatus[7].PktSubType = 4;
    adapter.TxSCtl.TxSStatus[7].TxRate = 42;
    adapter.TxSCtl.TxSStatus[7].Priv = 0x12345678;
    adapter.TxSCtl.TxSStatus[12].TxRate = 99;
    assert(RemoveTxSStatus(&adapter, 7, &type, &pktpid, &pkttype,
                           &subtype, &rate, &priv) == 0);
    assert(type == 1 && pktpid == 2 && pkttype == 3 && subtype == 4);
    assert(rate == 42 && priv == 0x12345678);
    assert(adapter.TxSCtl.TxSStatus[7].State == TXS_CLAIMED);
    assert(WrTxSCompleteClaim(&adapter, 7) == 0);
    assert(adapter.TxSCtl.TxSStatus[7].State == TXS_UNUSED);
    assert(!adapter.TxSCtl.TxSStatusLock.held);
    type = 77; rate = 77; priv = 77;
    assert(RemoveTxSStatus(&adapter, 7, &type, &pktpid, &pkttype,
                           &subtype, &rate, &priv) == -1);
    assert(type == 77 && rate == 77 && priv == 77);
    assert(!adapter.TxSCtl.TxSStatusLock.held);
    assert(RemoveTxSStatus(&adapter, 8, &type, &pktpid, &pkttype,
                           &subtype, &rate, &priv) == -1);
    assert(!adapter.TxSCtl.TxSStatusLock.held);
    assert(AddTxSStatus(&adapter, 1, 2, 3, 4, 56, 0xabcdef, &issued, &generation) == 0);
    assert(issued == 12);
    assert(generation != 0 && adapter.TxSCtl.TxSStatus[12].Generation == generation);
    assert(adapter.TxSCtl.TxSPid == 13 && !adapter.TxSCtl.TxSStatusLock.held);
    assert(adapter.TxSCtl.TxSStatus[12].State == TXS_USED);
    assert(adapter.TxSCtl.TxSStatus[12].TxRate == 56);
    adapter.TxSCtl.TxSPid = 255;
    assert(AddTxSStatus(&adapter, 1, 2, 3, 4, 78, 0xbeef, &issued, &generation) == 0);
    assert(issued == 255);
    assert(adapter.TxSCtl.TxSPid == 0 && !adapter.TxSCtl.TxSStatusLock.held);
    adapter.TxSCtl.TxSPid = 13;
    adapter.TxSCtl.TxSStatus[13].State = TXS_USED;
    adapter.TxSCtl.TxSStatus[13].Priv = 0xdeadbeef;
    assert(AddTxSStatus(&adapter, 1, 2, 3, 4, 80, 0xabcd, &issued, &generation) == 0);
    assert(issued == 14 && adapter.TxSCtl.TxSPid == 15);
    assert(CancelTxSReservation(&adapter, issued, generation - 1) == -1);
    assert(adapter.TxSCtl.TxSStatus[issued].State == TXS_USED);
    assert(CancelTxSReservation(&adapter, issued, generation) == 0);
    assert(adapter.TxSCtl.TxSStatus[issued].State == TXS_UNUSED);
    assert(CancelTxSReservation(&adapter, issued, generation) == -1);
    assert(!adapter.TxSCtl.TxSStatusLock.held);
    assert(adapter.TxSCtl.TxSStatus[13].Priv == 0xdeadbeef);
    for (i = 0; i < TXS_STATUS_NUM; i++) adapter.TxSCtl.TxSStatus[i].State = TXS_USED;
    issued = 77;
    assert(AddTxSStatus(&adapter, 1, 2, 3, 4, 90, 0xffff, &issued, &generation) == -1);
    assert(issued == 77 && adapter.TxSCtl.TxSFailCount == 1);
    assert(!adapter.TxSCtl.TxSStatusLock.held);
    puts("TxS allocation, generation-tagged cancellation, exhaustion and completion cases passed");
    return 0;
}
'''
    if args.output.exists():
        raise SystemExit("Fixture output already exists")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header + "\n".join(functions) + body, encoding="utf-8")


if __name__ == "__main__":
    main()
