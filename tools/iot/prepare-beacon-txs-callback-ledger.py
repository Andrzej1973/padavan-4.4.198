#!/usr/bin/env python3
"""Stage a bounded beacon TxS callback ledger; no hardware or close proof."""
import argparse
import hashlib
import json
from pathlib import Path


def once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise SystemExit('Changed beacon TxS anchor: ' + old[:80])
    return source.replace(old, new, 1)


def function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise SystemExit('Changed beacon TxS function: ' + signature)
    start = source.index(signature)
    return source[start:source.index('\n}', start) + 2]


parser = argparse.ArgumentParser()
parser.add_argument('candidate', type=Path, help='existing isolated driver directory')
parser.add_argument('output', type=Path, help='new overlay directory')
args = parser.parse_args()
root = args.candidate.resolve()
out = args.output.resolve()
if out.exists() or root == out or root in out.parents or out in root.parents:
    raise SystemExit('Output must be new and separate')
txs_path = root / 'tx_rx/txs.c'
header_path = root / 'include/mac/mac_mt/mt_mac.h'
originals = {txs_path: txs_path.read_bytes(), header_path: header_path.read_bytes()}
txs = originals[txs_path].decode('utf-8')
header = originals[header_path].decode('utf-8')

header = once(header,
              '\tNDIS_SPIN_LOCK TxSStatusLock;\n\tUINT32 ReservationGeneration;',
              '\tNDIS_SPIN_LOCK TxSStatusLock;\n'
              '\tUINT16 BeaconCallbacksInFlight[HW_BEACON_MAX_NUM];\n'
              '\tBOOLEAN BeaconCallbackAccountingFault;\n'
              '\tUINT32 ReservationGeneration;')
header = once(header,
              'UINT8 *PktSubType, UINT16 *TxRate, UINT32 *Priv);\n\n#define TSO_SIZE',
              'UINT8 *PktSubType, UINT16 *TxRate, UINT32 *Priv);\n'
              'INT32 WrBeaconTxSOutstanding(struct _RTMP_ADAPTER *pAd, UINT32 BssId);\n\n'
              '#define TSO_SIZE')

remove_sig = 'INT32 RemoveTxSStatus(RTMP_ADAPTER *pAd, UINT8 TxSPid,'
remove = function(txs, remove_sig)
remove = once(remove,
              '\t*TxSPriv = TxSCtl->TxSStatus[TxSPid].Priv;\n'
              '\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;',
              '\t*TxSPriv = TxSCtl->TxSStatus[TxSPid].Priv;\n'
              '\t/* Reserve callback ownership before releasing the PID. */\n'
              '\tif (*Type == TXS_TYPE1 && *PktType == FC_TYPE_MGMT &&\n'
              '\t    *PktSubType == SUBTYPE_BEACON && *TxSPriv < HW_BEACON_MAX_NUM) {\n'
              '\t\tif (TxSCtl->BeaconCallbacksInFlight[*TxSPriv] == 0xffffU) {\n'
              '\t\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);\n'
              '\t\t\treturn -1;\n'
              '\t\t}\n'
              '\t\tTxSCtl->BeaconCallbacksInFlight[*TxSPriv]++;\n'
              '\t}\n'
              '\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;')
txs = once(txs, function(txs, remove_sig), remove)
txs = once(txs,
           '\tNdisAllocateSpinLock(pAd, &TxSCtl->TxSStatusLock);\n'
           '\tfor (Index = 0; Index < TXS_STATUS_NUM; Index++)',
           '\tNdisAllocateSpinLock(pAd, &TxSCtl->TxSStatusLock);\n'
           '\tNdisZeroMemory(TxSCtl->BeaconCallbacksInFlight,\n'
           '\t               sizeof(TxSCtl->BeaconCallbacksInFlight));\n'
           '\tTxSCtl->BeaconCallbackAccountingFault = FALSE;\n'
           '\tfor (Index = 0; Index < TXS_STATUS_NUM; Index++)')

done = '''static VOID wr_beacon_txs_callback_done(RTMP_ADAPTER *pAd, UINT8 Type,
                                            UINT8 PktType, UINT8 PktSubType,
                                            UINT32 BssId)
{
    TXS_CTL *ctl;
    ULONG flags;

    if (Type != TXS_TYPE1 || PktType != FC_TYPE_MGMT ||
        PktSubType != SUBTYPE_BEACON || BssId >= HW_BEACON_MAX_NUM)
        return;
    ctl = &pAd->TxSCtl;
    RTMP_SPIN_LOCK_IRQSAVE(&ctl->TxSStatusLock, &flags);
    if (ctl->BeaconCallbacksInFlight[BssId])
        ctl->BeaconCallbacksInFlight[BssId]--;
    else
        ctl->BeaconCallbackAccountingFault = TRUE;
    RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->TxSStatusLock, &flags);
}

'''
parse_sig = 'INT32 ParseTxSPacket(RTMP_ADAPTER *pAd, UINT32 Pid,'
parse = function(txs, parse_sig)
parse = once(parse,
             'RTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
             '                        return -1;',
             'RTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
             '\t\t\twr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
             '                        return -1;')
parse = once(parse,
             '\t\t\t\tTxSType->TxSHandler(pAd, Data, Priv);\n\t\t\t\treturn 0;',
             '\t\t\t\tTxSType->TxSHandler(pAd, Data, Priv);\n'
             '\t\t\t\twr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
             '\t\t\t\treturn 0;')
parse = once(parse,
             '\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
             '\t}\n\n\treturn -1;',
             '\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
             '\t\twr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
             '\t}\n\n\treturn -1;')
txs = once(txs, function(txs, parse_sig), done + parse)

query = '''
/* A zero here is only a software snapshot, never RF or late-report proof. */
INT32 WrBeaconTxSOutstanding(RTMP_ADAPTER *pAd, UINT32 BssId)
{
    TXS_CTL *ctl;
    ULONG flags;
    UINT32 pid;
    INT32 result = 0;

    if (!pAd || BssId >= HW_BEACON_MAX_NUM)
        return -1;
    ctl = &pAd->TxSCtl;
    RTMP_SPIN_LOCK_IRQSAVE(&ctl->TxSStatusLock, &flags);
    if (ctl->BeaconCallbackAccountingFault) {
        RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->TxSStatusLock, &flags);
        return -1;
    }
    if (ctl->BeaconCallbacksInFlight[BssId])
        result = 1;
    for (pid = 0; pid < TXS_STATUS_NUM && !result; pid++) {
        TXS_STATUS *status = &ctl->TxSStatus[pid];
        if (status->State == TXS_USED && status->Type == TXS_TYPE1 &&
            status->PktType == FC_TYPE_MGMT &&
            status->PktSubType == SUBTYPE_BEACON && status->Priv == BssId)
            result = 1;
    }
    RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->TxSStatusLock, &flags);
    return result;
}
'''
txs = once(txs, function(txs, remove_sig), function(txs, remove_sig) + query)

for path, before in originals.items():
    if path.read_bytes() != before:
        raise SystemExit('Input changed during preparation')
for relative, content in (('tx_rx/txs.c', txs),
                          ('include/mac/mac_mt/mt_mac.h', header)):
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
manifest = {
    'source_sha256': {path.relative_to(root).as_posix(): hashlib.sha256(data).hexdigest()
                      for path, data in originals.items()},
    'output_sha256': {relative: hashlib.sha256((out / relative).read_bytes()).hexdigest()
                      for relative in ('tx_rx/txs.c', 'include/mac/mac_mt/mt_mac.h')},
    'callback_ledger_staged': True,
    'close_barrier_bound': False,
    'late_pid_reuse_safe': False,
    'target_compiled': False,
    'runtime_verified': False,
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                   encoding='utf-8')
print('Staged beacon callback ledger overlay; no close, PID-reuse or runtime proof')
