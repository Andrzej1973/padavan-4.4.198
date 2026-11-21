#!/usr/bin/env python3
"""Extract actual staged TxS ledger functions for a host-only race fixture."""
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument('overlay', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--expect-generation-exhaustion', action='store_true',
                    help='require fail-closed UINT32 exhaustion in the extracted allocator')
args = parser.parse_args()
if args.output.exists():
    raise SystemExit('Fixture output must be new')
source = (args.overlay / 'tx_rx/txs.c').read_text(encoding='utf-8')
functions = []
for signature in (
        'INT32 AddTxSStatus(RTMP_ADAPTER *pAd,',
        'INT32 RemoveTxSStatus(RTMP_ADAPTER *pAd,',
        'static INT32 WrTxSCompleteClaim(RTMP_ADAPTER *pAd,',
        'static VOID wr_beacon_txs_callback_done(RTMP_ADAPTER *pAd,',
        'INT32 WrBeaconTxSOutstanding(RTMP_ADAPTER *pAd,',
        'INT32 CancelTxSReservation(RTMP_ADAPTER *pAd,',
        'INT32 ParseTxSPacket(RTMP_ADAPTER *pAd,'):
    if source.count(signature) != 1:
        raise SystemExit('Missing staged function: ' + signature)
    start = source.index(signature)
    functions.append(source[start:source.index('\n}', start) + 2])
for anchor in (
        'wr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);',
        'NdisZeroMemory(TxSCtl->BeaconCallbacksInFlight,'):
    expected = 3 if anchor.startswith('wr_beacon_') else 1
    if source.count(anchor) != expected:
        raise SystemExit('Changed parser/init ledger anchor: ' + anchor)

header = r'''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;
typedef char CHAR;
typedef int INT32;
typedef uint8_t UINT8;
typedef uint16_t UINT16;
typedef uint32_t UINT32;
typedef unsigned long ULONG;
#define TXS_UNUSED 0
#define TXS_USED 1
#define TXS_CLAIMED 2
#define TXS_STATUS_NUM 256
#define TXS_TYPE0 0
#define TXS_TYPE1 1
#define TRUE 1
#define FALSE 0
#define FC_TYPE_MGMT 0
#define SUBTYPE_BEACON 8
#define HW_BEACON_MAX_NUM 16
#define TOTAL_PID_HASH_NUMS 16
#define TOTAL_PID_HASH_NUMS_PER_PKT_TYPE 8
#define TXS_DUMP_REPEAT 0xffffffffU
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_OFF 0
#define DBGPRINT(level,args) ((void)0)
#define printk(...) ((void)0)
static void DumpTxSFormat(void *ad, UINT8 format, char *data)
{ (void)ad; (void)format; (void)data; }
typedef struct { int held; } NDIS_SPIN_LOCK;
static NDIS_SPIN_LOCK *poison_lock;
static int poison_on_unlock;
static void poison_handler_registration(void);
#define RTMP_SPIN_LOCK_IRQSAVE(lock,flags) do {*(flags)=0;assert(!(lock)->held);(lock)->held=1;} while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock,flags) do {\
    (void)*(flags);assert((lock)->held);(lock)->held=0;\
    if ((lock)==poison_lock && poison_on_unlock) {\
        poison_on_unlock=0;poison_handler_registration();\
    }\
} while(0)
typedef struct {UINT8 TxSPid,State,Type,PktPid,PktType,PktSubType;
                UINT16 TxRate;UINT32 Priv,Generation;} TXS_STATUS;
typedef struct { int dummy; } DL_LIST;
struct adapter;
typedef INT32 (*TXS_HANDLER)(struct adapter *, char *, UINT32);
typedef struct txs_type {
    DL_LIST List;
    UINT8 PktPid,PktType,PktSubType,Format;
    int DumpTxSReport;
    UINT32 DumpTxSReportTimes;
    TXS_HANDLER TxSHandler;
} TXS_TYPE;
static TXS_TYPE handler;
static int use_handler;
static void poison_handler_registration(void) { handler.TxSHandler = NULL; }
#define DlListFirst(list,type,member) (use_handler ? &handler : NULL)
#define DlListForEach(item,list,type,member) \
    for ((item) = use_handler ? &handler : NULL; (item) != NULL; (item) = NULL)
typedef struct {UINT8 TxSPid;ULONG TxSFailCount;
                TXS_STATUS TxSStatus[TXS_STATUS_NUM];
                NDIS_SPIN_LOCK TxSStatusLock;
                UINT16 BeaconCallbacksInFlight[HW_BEACON_MAX_NUM];
                int BeaconCallbackAccountingFault;
                UINT32 ReservationGeneration;
                int TxSValid;
                NDIS_SPIN_LOCK TxSTypePerPktLock[TOTAL_PID_HASH_NUMS];
                DL_LIST TxSTypePerPkt[TOTAL_PID_HASH_NUMS];
                NDIS_SPIN_LOCK TxSTypePerPktTypeLock[3][TOTAL_PID_HASH_NUMS_PER_PKT_TYPE];
                DL_LIST TxSTypePerPktType[3][TOTAL_PID_HASH_NUMS_PER_PKT_TYPE];
                } TXS_CTL;
typedef struct adapter {TXS_CTL TxSCtl;} RTMP_ADAPTER;
'''
body = r'''
static RTMP_ADAPTER *current;
static int handler_calls, type0_calls, stale_report_misattributions;
static UINT8 current_pid;
static INT32 mock_type0(RTMP_ADAPTER *ad, char *data, UINT32 priv)
{
    (void)data;
    assert(ad == current && priv == 2);
    assert(ad->TxSCtl.TxSStatus[current_pid].State == TXS_CLAIMED);
    type0_calls++;
    return 0;
}
static INT32 mock_handler(RTMP_ADAPTER *ad, char *data, UINT32 bss)
{
    UINT8 next_pid;
    UINT32 next_generation;
    (void)data;
    assert(ad == current && bss == 2);
    assert(ad->TxSCtl.TxSStatus[current_pid].State == TXS_CLAIMED);
    assert(WrBeaconTxSOutstanding(ad, 2) == 1);
    ad->TxSCtl.TxSPid = current_pid;
    assert(AddTxSStatus(ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 1, &next_pid, &next_generation) == 0);
    assert(next_pid != current_pid);
    assert(CancelTxSReservation(ad, next_pid, next_generation) == 0);
    handler_calls++;
    return 0;
}
/* Negative witness: the report supplies only the old PID, not Generation. */
static INT32 mock_stale_report_handler(RTMP_ADAPTER *ad, char *data, UINT32 bss)
{
    (void)data;
    assert(ad == current && bss == 3);
    assert(ad->TxSCtl.TxSStatus[current_pid].State == TXS_CLAIMED);
    stale_report_misattributions++;
    return 0;
}
int main(void)
{
    RTMP_ADAPTER ad = {0};
    UINT8 pid, old_pid, type, pktpid, pkt_type, subtype;
    UINT16 rate;
    UINT32 generation, old_generation, bss;

    assert(WrBeaconTxSOutstanding(&ad, 16) == -1);
    assert(WrBeaconTxSOutstanding(NULL, 2) == -1);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);
    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 1);
    assert(WrBeaconTxSOutstanding(&ad, 1) == 0);
    assert(RemoveTxSStatus(&ad, pid, &type, &pktpid, &pkt_type,
                           &subtype, &rate, &bss) == 0);
    assert(bss == 2 && ad.TxSCtl.TxSStatus[pid].State == TXS_CLAIMED);
    assert(ad.TxSCtl.BeaconCallbacksInFlight[2] == 1);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 1);
    wr_beacon_txs_callback_done(&ad, type, pkt_type, subtype, bss);
    assert(ad.TxSCtl.BeaconCallbacksInFlight[2] == 0);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 1);
    assert(WrTxSCompleteClaim(&ad, pid) == 0);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);
    wr_beacon_txs_callback_done(&ad, type, pkt_type, subtype, bss);
    assert(ad.TxSCtl.BeaconCallbackAccountingFault);
    assert(WrBeaconTxSOutstanding(&ad, 2) == -1);
    ad.TxSCtl.BeaconCallbackAccountingFault = FALSE;

    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(CancelTxSReservation(&ad, pid, generation) == 0);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);

    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, 1, 0, 42, 2,
                        &pid, &generation) == 0);
    assert(RemoveTxSStatus(&ad, pid, &type, &pktpid, &pkt_type,
                           &subtype, &rate, &bss) == 0);
    assert(WrTxSCompleteClaim(&ad, pid) == 0);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);

    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    ad.TxSCtl.BeaconCallbacksInFlight[2] = UINT16_MAX;
    assert(RemoveTxSStatus(&ad, pid, &type, &pktpid, &pkt_type,
                           &subtype, &rate, &bss) == -1);
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_USED);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 1);
    assert(!ad.TxSCtl.TxSStatusLock.held);
    ad.TxSCtl.BeaconCallbacksInFlight[2] = 0;
    ad.TxSCtl.TxSStatus[pid].State = TXS_UNUSED;
    ad.TxSCtl.TxSValid = TRUE;
    current = &ad;
    use_handler = 1;
    memset(&handler, 0, sizeof(handler));
    handler.PktType = FC_TYPE_MGMT;
    handler.PktSubType = SUBTYPE_BEACON;
    handler.Format = 0;
    handler.TxSHandler = mock_handler;
    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    current_pid = pid;
    poison_lock = &ad.TxSCtl.TxSTypePerPktTypeLock[FC_TYPE_MGMT]
        [SUBTYPE_BEACON % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE];
    poison_on_unlock = 1;
    assert(ParseTxSPacket(&ad, pid, 0, "") == 0);
    assert(!poison_on_unlock && handler.TxSHandler == NULL);
    handler.TxSHandler = mock_handler;
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    assert(handler_calls == 1 && WrBeaconTxSOutstanding(&ad, 2) == 0);
    old_pid = pid;
    old_generation = generation;
    ad.TxSCtl.TxSPid = old_pid;
    handler.TxSHandler = mock_stale_report_handler;
    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 3, &pid, &generation) == 0);
    assert(pid == old_pid && generation != old_generation);
    assert(WrBeaconTxSOutstanding(&ad, 3) == 1);
    current_pid = pid;
    /* Model a duplicate old hardware report before the new transmission reports. */
    assert(ParseTxSPacket(&ad, old_pid, 0, "") == 0);
    assert(stale_report_misattributions == 1);
    assert(WrBeaconTxSOutstanding(&ad, 3) == 0);
    assert(ParseTxSPacket(&ad, pid, 0, "") == -1);
    handler.TxSHandler = mock_handler;
    use_handler = 0;
    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(ParseTxSPacket(&ad, pid, 0, "") == -1);
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);
    use_handler = 1;
    assert(AddTxSStatus(&ad, TXS_TYPE1, 0, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(ParseTxSPacket(&ad, pid, 1, "") == -1);
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    assert(WrBeaconTxSOutstanding(&ad, 2) == 0);
    use_handler = 1;
    memset(&handler, 0, sizeof(handler));
    handler.PktPid = 5;
    handler.Format = 0;
    handler.TxSHandler = mock_type0;
    assert(AddTxSStatus(&ad, TXS_TYPE0, 5, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    current_pid = pid;
    assert(ParseTxSPacket(&ad, pid, 0, "") == 0);
    assert(type0_calls == 1 && ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    use_handler = 0;
    assert(AddTxSStatus(&ad, TXS_TYPE0, 5, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(ParseTxSPacket(&ad, pid, 0, "") == -1);
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    assert(AddTxSStatus(&ad, 2, 5, FC_TYPE_MGMT,
                        SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
    assert(ParseTxSPacket(&ad, pid, 0, "") == -1);
    assert(ad.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    assert(ParseTxSPacket(&ad, TXS_STATUS_NUM, 0, "") == -1);
    {
        RTMP_ADAPTER wrapped = {0};
        /* Software cancellation identity also repeats after UINT32 wrap. */
        wrapped.TxSCtl.ReservationGeneration = UINT32_MAX;
        assert(AddTxSStatus(&wrapped, TXS_TYPE1, 0, FC_TYPE_MGMT,
                           SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
        assert(generation == 1);
        assert(CancelTxSReservation(&wrapped, pid, 1) == 0);
        assert(wrapped.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);
    }
    puts("PASS extracted TxS ledger/parser; NEGATIVE WITNESSES: stale PID report and wrapped cancellation identity; no RF proof");
    return 0;
}
'''
args.output.parent.mkdir(parents=True, exist_ok=True)
if args.expect_generation_exhaustion:
    old = '''        assert(AddTxSStatus(&wrapped, TXS_TYPE1, 0, FC_TYPE_MGMT,
                           SUBTYPE_BEACON, 42, 2, &pid, &generation) == 0);
        assert(generation == 1);
        assert(CancelTxSReservation(&wrapped, pid, 1) == 0);
        assert(wrapped.TxSCtl.TxSStatus[pid].State == TXS_UNUSED);'''
    new = '''        pid = 77; generation = 99;
        assert(AddTxSStatus(&wrapped, TXS_TYPE1, 0, FC_TYPE_MGMT,
                           SUBTYPE_BEACON, 42, 2, &pid, &generation) == -1);
        assert(pid == 77 && generation == 99);
        assert(wrapped.TxSCtl.ReservationGeneration == UINT32_MAX);
        assert(wrapped.TxSCtl.TxSStatus[0].State == TXS_UNUSED);
        assert(!wrapped.TxSCtl.TxSStatusLock.held);'''
    assert body.count(old) == 1
    body = body.replace(old, new).replace(
        'stale PID report and wrapped cancellation identity',
        'stale PID report; generation exhaustion refused')
args.output.write_text(header + '\n'.join(functions) + body,
                       encoding='utf-8')
print('Prepared host-only beacon TxS ledger fixture')
